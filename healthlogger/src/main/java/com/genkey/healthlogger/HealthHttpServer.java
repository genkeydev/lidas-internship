package com.genkey.healthlogger;

import com.genkey.healthlogger.model.HealthEvent;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

/**
 * Tiny local HTTP surface (JDK HttpServer, not a servlet container).
 *
 * POST /events — record a valid event or save a rejected submission.
 * GET /health  — liveness check.
 */
public final class HealthHttpServer {

    /**
     * Maximum HTTP request body accepted by the server.
     * Requests larger than this are rejected with HTTP 413.
     */
    public static final int MAX_REQUEST_BODY_BYTES = 1024 * 1024;

    private final ClientSpec spec;
    private final JsonlStore store;
    private final RejectedEventStore rejectedStore;
    private HttpServer server;

    public HealthHttpServer(
            ClientSpec spec,
            JsonlStore store,
            RejectedEventStore rejectedStore
    ) {
        this.spec = spec;
        this.store = store;
        this.rejectedStore = rejectedStore;
    }

    public void start() throws IOException {
        server = HttpServer.create(
                new InetSocketAddress("127.0.0.1", spec.port()),
                0
        );

        server.createContext("/health", this::health);
        server.createContext("/events", this::events);

        server.start();

        System.err.println(
                "listening on http://127.0.0.1:" + spec.port()
        );
    }

    public void stop() {
        if (server != null) {
            server.stop(0);
        }
    }

    private void health(HttpExchange ex) throws IOException {
        if (!"GET".equals(ex.getRequestMethod())) {
            send(
                    ex,
                    405,
                    "{\"error\":\"method not allowed\"}"
            );
            return;
        }

        send(
                ex,
                200,
                "{\"status\":\"ok\"}"
        );
    }

    private void events(HttpExchange ex) throws IOException {
        if (!"POST".equals(ex.getRequestMethod())) {
            send(
                    ex,
                    405,
                    "{\"error\":\"method not allowed\"}"
            );
            return;
        }

        byte[] bodyBytes;

        try {
            bodyBytes = readRequestBody(
                    ex.getRequestBody(),
                    MAX_REQUEST_BODY_BYTES
            );
        } catch (RequestTooLargeException e) {
            send(
                    ex,
                    413,
                    "{\"error\":\"request body too large\"}"
            );
            return;
        }

        String body = new String(
                bodyBytes,
                StandardCharsets.UTF_8
        );

        HealthEvent event;

        try {
            event = Json.parseEvent(body);
        } catch (Exception e) {
            rejectedStore.append(
                    body,
                    "malformed JSON: " + e.getMessage()
            );

            send(
                    ex,
                    400,
                    Json.toJson(
                            Map.of(
                                    "error",
                                    "malformed JSON"
                            )
                    )
            );
            return;
        }

        List<String> issues = Json.validate(event, spec);

        if (!issues.isEmpty()) {
            rejectedStore.append(
                    event.fields(),
                    String.join("; ", issues)
            );

            send(
                    ex,
                    400,
                    Json.toJson(
                            Map.of(
                                    "issues",
                                    issues
                            )
                    )
            );
            return;
        }

        store.append(event);

        StructuredLogger.event(spec, event);

        send(
                ex,
                201,
                Json.toJson(event.fields())
        );
    }

    private static byte[] readRequestBody(
            InputStream input,
            int maxBytes
    ) throws IOException, RequestTooLargeException {

        ByteArrayOutputStream output =
                new ByteArrayOutputStream();

        byte[] buffer = new byte[8192];

        int total = 0;
        int bytesRead;

        while ((bytesRead = input.read(buffer)) != -1) {

            total += bytesRead;

            if (total > maxBytes) {
                throw new RequestTooLargeException();
            }

            output.write(
                    buffer,
                    0,
                    bytesRead
            );
        }

        return output.toByteArray();
    }

    private static void send(
            HttpExchange ex,
            int code,
            String json
    ) throws IOException {

        byte[] bytes = json.getBytes(
                StandardCharsets.UTF_8
        );

        ex.getResponseHeaders().set(
                "Content-Type",
                "application/json"
        );

        ex.sendResponseHeaders(
                code,
                bytes.length
        );

        try (OutputStream os = ex.getResponseBody()) {
            os.write(bytes);
        }
    }

    private static final class RequestTooLargeException
            extends Exception {

        private RequestTooLargeException() {
            super("request body exceeds maximum size");
        }
    }
}
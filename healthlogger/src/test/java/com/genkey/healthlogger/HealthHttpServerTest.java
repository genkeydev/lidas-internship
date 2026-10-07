package com.genkey.healthlogger;

import com.genkey.healthlogger.model.HealthEvent;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.net.ServerSocket;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class HealthHttpServerTest {

    @Test
    void healthEndpointReturns200() throws Exception {
        Path tempDir = Files.createTempDirectory("healthlogger-http-test");
        Path eventsPath = tempDir.resolve("events.jsonl");
        Path rejectedPath = tempDir.resolve("rejected-events.jsonl");

        int port = findFreePort();

        ClientSpec spec = testSpec(port);
        JsonlStore store = new JsonlStore(eventsPath);
        RejectedEventStore rejectedStore =
                new RejectedEventStore(rejectedPath);

        HealthHttpServer server =
                new HealthHttpServer(spec, store, rejectedStore);

        server.start();

        try {
            HttpResponse<String> response = send(
                    "GET",
                    port,
                    "/health",
                    null
            );

            assertEquals(200, response.statusCode());
            assertEquals(
                    "{\"status\":\"ok\"}",
                    response.body()
            );
        } finally {
            server.stop();
        }
    }

    @Test
    void postEventsCreatesRecord() throws Exception {
        Path tempDir = Files.createTempDirectory("healthlogger-http-test");
        Path eventsPath = tempDir.resolve("events.jsonl");
        Path rejectedPath = tempDir.resolve("rejected-events.jsonl");

        int port = findFreePort();

        ClientSpec spec = testSpec(port);
        JsonlStore store = new JsonlStore(eventsPath);
        RejectedEventStore rejectedStore =
                new RejectedEventStore(rejectedPath);

        HealthHttpServer server =
                new HealthHttpServer(spec, store, rejectedStore);

        server.start();

        try {
            String body = """
                    {
                      "service": "payments-api",
                      "status": "ok",
                      "timestamp": "2026-09-29T10:00:00Z"
                    }
                    """;

            HttpResponse<String> response = send(
                    "POST",
                    port,
                    "/events",
                    body
            );

            assertEquals(201, response.statusCode());

            List<HealthEvent> events = store.query(null);

            assertEquals(1, events.size());
            assertEquals(
                    "payments-api",
                    events.get(0).service()
            );
            assertEquals(
                    "ok",
                    events.get(0).status()
            );

            assertFalse(
                    Files.exists(rejectedPath)
            );
        } finally {
            server.stop();
        }
    }

    @Test
    void postEventsRejectsIncompleteBodyAndSavesRejection()
            throws Exception {

        Path tempDir = Files.createTempDirectory("healthlogger-http-test");
        Path eventsPath = tempDir.resolve("events.jsonl");
        Path rejectedPath = tempDir.resolve("rejected-events.jsonl");

        int port = findFreePort();

        ClientSpec spec = testSpec(port);
        JsonlStore store = new JsonlStore(eventsPath);
        RejectedEventStore rejectedStore =
                new RejectedEventStore(rejectedPath);

        HealthHttpServer server =
                new HealthHttpServer(spec, store, rejectedStore);

        server.start();

        try {
            String body = """
                    {
                      "service": "payments-api",
                      "status": "ok"
                    }
                    """;

            HttpResponse<String> response = send(
                    "POST",
                    port,
                    "/events",
                    body
            );

            assertEquals(400, response.statusCode());

            assertTrue(
                    store.query(null).isEmpty()
            );

            assertTrue(
                    Files.exists(rejectedPath)
            );

            String rejection =
                    Files.readString(rejectedPath);

            assertTrue(
                    rejection.contains("payments-api")
            );

            assertTrue(
                    rejection.contains("timestamp")
            );

            assertTrue(
                    rejection.contains(
                            "missing required field: timestamp"
                    )
            );
        } finally {
            server.stop();
        }
    }

    @Test
    void postEventsRejectsMalformedJsonAndSavesRejection()
            throws Exception {

        Path tempDir = Files.createTempDirectory("healthlogger-http-test");
        Path eventsPath = tempDir.resolve("events.jsonl");
        Path rejectedPath = tempDir.resolve("rejected-events.jsonl");

        int port = findFreePort();

        ClientSpec spec = testSpec(port);
        JsonlStore store = new JsonlStore(eventsPath);
        RejectedEventStore rejectedStore =
                new RejectedEventStore(rejectedPath);

        HealthHttpServer server =
                new HealthHttpServer(spec, store, rejectedStore);

        server.start();

        try {
            String body =
                    "{\"service\":\"payments-api\",\"status\":\"ok\"";

            HttpResponse<String> response = send(
                    "POST",
                    port,
                    "/events",
                    body
            );

            assertEquals(400, response.statusCode());

            assertTrue(
                    store.query(null).isEmpty()
            );

            assertTrue(
                    Files.exists(rejectedPath)
            );

            String rejection =
                    Files.readString(rejectedPath);

            assertTrue(
                    rejection.contains("payments-api")
            );

            assertTrue(
                    rejection.contains("malformed JSON")
            );
        } finally {
            server.stop();
        }
    }

    @Test
    void postEventsRejectsEmptyBodyAndSavesRejection()
            throws Exception {

        Path tempDir = Files.createTempDirectory("healthlogger-http-test");
        Path eventsPath = tempDir.resolve("events.jsonl");
        Path rejectedPath = tempDir.resolve("rejected-events.jsonl");

        int port = findFreePort();

        ClientSpec spec = testSpec(port);
        JsonlStore store = new JsonlStore(eventsPath);
        RejectedEventStore rejectedStore =
                new RejectedEventStore(rejectedPath);

        HealthHttpServer server =
                new HealthHttpServer(spec, store, rejectedStore);

        server.start();

        try {
            HttpResponse<String> response = send(
                    "POST",
                    port,
                    "/events",
                    ""
            );

            assertEquals(400, response.statusCode());

            assertTrue(
                    store.query(null).isEmpty()
            );

            assertTrue(
                    Files.exists(rejectedPath)
            );

            String rejection =
                    Files.readString(rejectedPath);

            assertTrue(
                    rejection.contains("malformed JSON")
            );
        } finally {
            server.stop();
        }
    }

    @Test
    void postEventsRejectsHugePayload() throws Exception {
        Path tempDir = Files.createTempDirectory("healthlogger-http-test");
        Path eventsPath = tempDir.resolve("events.jsonl");
        Path rejectedPath = tempDir.resolve("rejected-events.jsonl");

        int port = findFreePort();

        ClientSpec spec = testSpec(port);
        JsonlStore store = new JsonlStore(eventsPath);
        RejectedEventStore rejectedStore =
                new RejectedEventStore(rejectedPath);

        HealthHttpServer server =
                new HealthHttpServer(spec, store, rejectedStore);

        server.start();

        try {
            String hugeBody = "x".repeat(
                    HealthHttpServer.MAX_REQUEST_BODY_BYTES + 1
            );

            HttpResponse<String> response = send(
                    "POST",
                    port,
                    "/events",
                    hugeBody
            );

            assertEquals(413, response.statusCode());

            assertTrue(
                    store.query(null).isEmpty()
            );
        } finally {
            server.stop();
        }
    }

    @Test
    void postEventsAcceptsExtraFields() throws Exception {
        Path tempDir = Files.createTempDirectory("healthlogger-http-test");
        Path eventsPath = tempDir.resolve("events.jsonl");
        Path rejectedPath = tempDir.resolve("rejected-events.jsonl");

        int port = findFreePort();

        ClientSpec spec = testSpec(port);
        JsonlStore store = new JsonlStore(eventsPath);
        RejectedEventStore rejectedStore =
                new RejectedEventStore(rejectedPath);

        HealthHttpServer server =
                new HealthHttpServer(spec, store, rejectedStore);

        server.start();

        try {
            String body = """
                    {
                      "service": "payments-api",
                      "status": "ok",
                      "timestamp": "2026-09-29T10:00:00Z",
                      "region": "accra",
                      "version": "2.1.0"
                    }
                    """;

            HttpResponse<String> response = send(
                    "POST",
                    port,
                    "/events",
                    body
            );

            assertEquals(201, response.statusCode());

            List<HealthEvent> events = store.query(null);

            assertEquals(1, events.size());

            Map<String, Object> fields =
                    events.get(0).fields();

            assertEquals(
                    "accra",
                    fields.get("region")
            );

            assertEquals(
                    "2.1.0",
                    fields.get("version")
            );
        } finally {
            server.stop();
        }
    }

    private static ClientSpec testSpec(int port) {
        return new ClientSpec(
                "1.0.0",
                "Test Client",
                List.of(
                        "service",
                        "status",
                        "timestamp"
                ),
                List.of(
                        "ok",
                        "degraded",
                        "down"
                ),
                Map.of(
                        "ok", "info",
                        "degraded", "warn",
                        "down", "error"
                ),
                port
        );
    }

    private static int findFreePort() throws IOException {
        try (ServerSocket socket = new ServerSocket(0)) {
            return socket.getLocalPort();
        }
    }

    private static HttpResponse<String> send(
            String method,
            int port,
            String path,
            String body
    ) throws Exception {

        HttpClient client = HttpClient.newHttpClient();

        HttpRequest.Builder builder =
                HttpRequest.newBuilder()
                        .uri(
                                URI.create(
                                        "http://127.0.0.1:"
                                                + port
                                                + path
                                )
                        );

        if ("POST".equals(method)) {
            builder.header(
                    "Content-Type",
                    "application/json"
            );

            builder.POST(
                    HttpRequest.BodyPublishers.ofString(
                            body == null ? "" : body
                    )
            );
        } else {
            builder.GET();
        }

        return client.send(
                builder.build(),
                HttpResponse.BodyHandlers.ofString()
        );
    }
}
package com.genkey.healthlogger;

import com.genkey.healthlogger.model.HealthEvent;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/**
 * CLI: {@code record}, {@code query}, {@code serve}.
 *
 * <pre>
 *   record [--spec path] [--store path] [--json-file event.json] '{"service":"..."}'
 *   query  [--spec path] [--store path] [--service name]
 *   serve  [--spec path] [--store path]
 * </pre>
 */
public final class HealthLoggerCli {

    public static void main(String[] args) {
        System.exit(run(args));
    }

    static int run(String[] args) {
        try {
            return runThrowing(args);
        } catch (Exception e) {
            System.err.println("error: " + e.getMessage());
            return 2;
        }
    }

    private static int runThrowing(String[] args) throws Exception {
        if (args.length == 0) {
            System.err.println("usage: healthlogger record|query|serve [options]");
            return 2;
        }
        String command = args[0];
        Path specPath = envOr("HEALTHLOGGER_SPEC", "config/client-spec.json");
        Path storePath = envOr("HEALTHLOGGER_STORE", "data/events.jsonl");
        String serviceFilter = null;
        String jsonBody = null;

        for (int i = 1; i < args.length; i++) {
            switch (args[i]) {
                case "--spec" -> specPath = Path.of(args[++i]);
                case "--store" -> storePath = Path.of(args[++i]);
                case "--service" -> serviceFilter = args[++i];
                case "--json-file" -> jsonBody = Files.readString(Path.of(args[++i]));
                default -> jsonBody = args[i];
            }
        }

        ClientSpec spec = Json.loadSpec(specPath);
        JsonlStore store = new JsonlStore(storePath);
        Path rejectedStorePath = Path.of("data/rejected-events.jsonl");
        RejectedEventStore rejectedStore = new RejectedEventStore(rejectedStorePath);
        return switch (command) {
            case "record" -> {
                if (jsonBody == null) {
                    System.err.println("error: pass a JSON object argument");
                    yield 2;
                }
                HealthEvent event = Json.parseEvent(jsonBody);
                List<String> issues = Json.validate(event, spec);
                if (!issues.isEmpty()) {
                    issues.forEach(msg -> System.err.println(msg));
                    yield 1;
                }
                store.append(event);
                StructuredLogger.event(spec, event);
                yield 0;
            }
            case "query" -> {
                for (HealthEvent event : store.query(serviceFilter)) {
                    System.out.println(Json.toJson(event.fields()));
                }
                yield 0;
            }
            case "serve" -> {
                HealthHttpServer http = new HealthHttpServer(spec, store,rejectedStore);
                http.start();
                Thread.currentThread().join();
                yield 0;
            }
            default -> {
                System.err.println("unknown command: " + command);
                yield 2;
            }
        };
    }

    private static Path envOr(String env, String fallback) {
        String v = System.getenv(env);
        if (v != null && !v.isBlank()) {
            return Path.of(v);
        }
        return Path.of(fallback);
    }
}

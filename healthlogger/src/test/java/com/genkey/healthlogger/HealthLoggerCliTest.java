package com.genkey.healthlogger;

import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.*;

class HealthLoggerCliTest {

    @Test
    void noArgumentsReturnsUsageError() {
        int result = HealthLoggerCli.run(new String[]{});

        assertEquals(2, result);
    }

    @Test
    void unknownCommandReturnsError() {
        int result = HealthLoggerCli.run(
                new String[]{"unknown"}
        );

        assertEquals(2, result);
    }

    @Test
    void recordWithoutJsonReturnsError() throws Exception {
        Path tempDir =
                Files.createTempDirectory("healthlogger-cli-test");

        Path specPath =
                createSpec(tempDir);

        Path storePath =
                tempDir.resolve("events.jsonl");

        int result = HealthLoggerCli.run(
                new String[]{
                        "record",
                        "--spec",
                        specPath.toString(),
                        "--store",
                        storePath.toString()
                }
        );

        assertEquals(2, result);
        assertFalse(Files.exists(storePath));
    }

    @Test
    void recordValidEventReturnsSuccess() throws Exception {
        Path tempDir =
                Files.createTempDirectory("healthlogger-cli-test");

        Path specPath =
                createSpec(tempDir);

        Path storePath =
                tempDir.resolve("events.jsonl");

        String json = """
                {
                  "service": "payments-api",
                  "status": "ok",
                  "timestamp": "2026-10-01T10:00:00Z"
                }
                """;

        int result = HealthLoggerCli.run(
                new String[]{
                        "record",
                        "--spec",
                        specPath.toString(),
                        "--store",
                        storePath.toString(),
                        json
                }
        );

        assertEquals(0, result);
        assertTrue(Files.exists(storePath));

        String stored =
                Files.readString(storePath);

        assertTrue(
                stored.contains("payments-api")
        );
        assertTrue(
                stored.contains("\"status\":\"ok\"")
        );
    }

    @Test
    void recordInvalidEventReturnsValidationError()
            throws Exception {

        Path tempDir =
                Files.createTempDirectory("healthlogger-cli-test");

        Path specPath =
                createSpec(tempDir);

        Path storePath =
                tempDir.resolve("events.jsonl");

        String json = """
                {
                  "service": "payments-api",
                  "status": "invalid"
                }
                """;

        int result = HealthLoggerCli.run(
                new String[]{
                        "record",
                        "--spec",
                        specPath.toString(),
                        "--store",
                        storePath.toString(),
                        json
                }
        );

        assertEquals(1, result);
        assertFalse(Files.exists(storePath));
    }

    @Test
    void recordFromJsonFileReturnsSuccess()
            throws Exception {

        Path tempDir =
                Files.createTempDirectory("healthlogger-cli-test");

        Path specPath =
                createSpec(tempDir);

        Path storePath =
                tempDir.resolve("events.jsonl");

        Path jsonFile =
                tempDir.resolve("event.json");

        Files.writeString(
                jsonFile,
                """
                {
                  "service": "orders-api",
                  "status": "degraded",
                  "timestamp": "2026-10-01T10:00:00Z"
                }
                """
        );

        int result = HealthLoggerCli.run(
                new String[]{
                        "record",
                        "--spec",
                        specPath.toString(),
                        "--store",
                        storePath.toString(),
                        "--json-file",
                        jsonFile.toString()
                }
        );

        assertEquals(0, result);
        assertTrue(Files.exists(storePath));

        String stored =
                Files.readString(storePath);

        assertTrue(
                stored.contains("orders-api")
        );
        assertTrue(
                stored.contains("\"status\":\"degraded\"")
        );
    }

    @Test
    void queryReturnsStoredEvents() throws Exception {
        Path tempDir =
                Files.createTempDirectory("healthlogger-cli-test");

        Path specPath =
                createSpec(tempDir);

        Path storePath =
                tempDir.resolve("events.jsonl");

        Files.writeString(
                storePath,
                """
                {"service":"payments-api","status":"ok","timestamp":"2026-10-01T10:00:00Z"}
                {"service":"orders-api","status":"down","timestamp":"2026-10-01T11:00:00Z"}
                """
        );

        int result = HealthLoggerCli.run(
                new String[]{
                        "query",
                        "--spec",
                        specPath.toString(),
                        "--store",
                        storePath.toString()
                }
        );

        assertEquals(0, result);
    }

    @Test
    void queryWithServiceFilterReturnsSuccess()
            throws Exception {

        Path tempDir =
                Files.createTempDirectory("healthlogger-cli-test");

        Path specPath =
                createSpec(tempDir);

        Path storePath =
                tempDir.resolve("events.jsonl");

        Files.writeString(
                storePath,
                """
                {"service":"payments-api","status":"ok","timestamp":"2026-10-01T10:00:00Z"}
                {"service":"orders-api","status":"down","timestamp":"2026-10-01T11:00:00Z"}
                """
        );

        int result = HealthLoggerCli.run(
                new String[]{
                        "query",
                        "--spec",
                        specPath.toString(),
                        "--store",
                        storePath.toString(),
                        "--service",
                        "payments-api"
                }
        );

        assertEquals(0, result);
    }

    private static Path createSpec(Path tempDir)
            throws Exception {

        Path specPath =
                tempDir.resolve("client-spec.json");

        Files.writeString(
                specPath,
                """
                {
                  "schemaVersion": "1.0.0",
                  "client": "Test Client",
                  "requiredFields": [
                    "service",
                    "status",
                    "timestamp"
                  ],
                  "allowedStatuses": [
                    "ok",
                    "degraded",
                    "down"
                  ],
                  "severityMap": {
                    "ok": "info",
                    "degraded": "warn",
                    "down": "error"
                  },
                  "httpPort": 0
                }
                """
        );

        return specPath;
    }
}

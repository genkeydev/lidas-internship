package com.genkey.configmaster;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class ConfigMasterCliTest {

    @TempDir
    Path tempDir;

    @Test
    void noArgumentsReturnsUsageError() {
        int exitCode = ConfigMasterCli.run(new String[]{});

        assertEquals(2, exitCode);
    }

    @Test
    void validateReturnsZeroForValidConfig() throws Exception {
        Path spec = writeSpec();
        Path config = tempDir.resolve("valid.json");

        Files.writeString(config, """
                {
                  "app": {
                    "port": 8080
                  }
                }
                """);

        int exitCode = ConfigMasterCli.run(new String[]{
                "validate",
                "--spec", spec.toString(),
                config.toString()
        });

        assertEquals(0, exitCode);
    }

    @Test
    void validateReturnsOneForSchemaIssue() throws Exception {
        Path spec = writeSpec();
        Path config = tempDir.resolve("invalid.json");

        Files.writeString(config, """
                {
                  "app": {
                    "port": "8080"
                  }
                }
                """);

        int exitCode = ConfigMasterCli.run(new String[]{
                "validate",
                "--spec", spec.toString(),
                config.toString()
        });

        assertEquals(1, exitCode);
    }

    @Test
    void showReturnsZeroForValidConfig() throws Exception {
        Path spec = writeSpec();
        Path config = tempDir.resolve("show.json");

        Files.writeString(config, """
                {
                  "app": {
                    "port": 8080
                  }
                }
                """);

        int exitCode = ConfigMasterCli.run(new String[]{
                "show",
                "--spec", spec.toString(),
                config.toString()
        });

        assertEquals(0, exitCode);
    }

    @Test
    void malformedJsonReturnsUsageError() throws Exception {
        Path spec = writeSpec();
        Path config = tempDir.resolve("broken.json");

        Files.writeString(config, """
                {
                  "app": {
                    "port": 8080
                """);

        int exitCode = ConfigMasterCli.run(new String[]{
                "validate",
                "--spec", spec.toString(),
                config.toString()
        });

        assertEquals(2, exitCode);
    }

    @Test
    void unknownCommandReturnsUsageError() throws Exception {
        Path spec = writeSpec();
        Path config = tempDir.resolve("valid.json");

        Files.writeString(config, """
                {
                  "app": {
                    "port": 8080
                  }
                }
                """);

        int exitCode = ConfigMasterCli.run(new String[]{
                "unknown",
                "--spec", spec.toString(),
                config.toString()
        });

        assertEquals(2, exitCode);
    }

    private Path writeSpec() throws Exception {
        Path spec = tempDir.resolve("client-spec.json");

        Files.writeString(spec, """
                {
                  "schemaVersion": "1.0",
                  "client": "GenKey",
                  "requiredFields": [
                    "app.port"
                  ],
                  "fieldTypes": {
                    "app.port": "integer"
                  },
                  "mergeStrategies": {},
                  "defaultMergeStrategy": "override"
                }
                """);

        return spec;
    }
}
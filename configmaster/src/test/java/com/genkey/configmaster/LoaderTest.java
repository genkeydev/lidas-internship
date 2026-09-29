package com.genkey.configmaster;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class LoaderTest {

    @TempDir
    Path tempDir;

    @Test
    void nullJsonBecomesEmptyDocument() throws Exception {
        Path file = tempDir.resolve("null.json");

        Files.writeString(file, "null");

        var document = Loader.loadJson(file);

        assertTrue(document.tree().isEmpty());
    }
}
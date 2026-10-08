package com.genkey.configmaster;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertThrows;
import org.junit.jupiter.api.Test;

class ClientSpecTest {

    @Test
    void acceptsCurrentSchemaVersion() {
        ClientSpec spec = specWithVersion("1.0.0");

        assertDoesNotThrow(spec::validateSchemaVersion);
    }

    @Test
    void acceptsCompatibleMinorAndPatchVersion() {
        ClientSpec spec = specWithVersion("1.2.3");

        assertDoesNotThrow(spec::validateSchemaVersion);
    }

    @Test
    void rejectsUnsupportedMajorVersion() {
        ClientSpec spec = specWithVersion("2.0.0");

        assertThrows(
                IllegalArgumentException.class,
                spec::validateSchemaVersion);
    }

    @Test
    void rejectsMalformedSchemaVersion() {
        ClientSpec spec = specWithVersion("abc");

        assertThrows(
                IllegalArgumentException.class,
                spec::validateSchemaVersion);
    }

    @Test
    void rejectsIncompleteSchemaVersion() {
        ClientSpec spec = specWithVersion("1.0");

        assertThrows(
                IllegalArgumentException.class,
                spec::validateSchemaVersion);
    }

    @Test
    void rejectsBlankSchemaVersion() {
        ClientSpec spec = specWithVersion("");

        assertThrows(
                IllegalArgumentException.class,
                spec::validateSchemaVersion);
    }

    @Test
    void rejectsMissingSchemaVersion() {
        ClientSpec spec = specWithVersion(null);

        assertThrows(
                IllegalArgumentException.class,
                spec::validateSchemaVersion);
    }

    private static ClientSpec specWithVersion(String version) {
        return new ClientSpec(
                version,
                "Test Client",
                List.of(),
                Map.of(),
                Map.of(),
                "override");
    }
}
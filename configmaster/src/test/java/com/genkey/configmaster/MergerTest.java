package com.genkey.configmaster;

import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.Test;

import com.genkey.configmaster.model.ConfigDocument;
import com.genkey.configmaster.model.MergeResult;

/**
 * Starter merge tests — extended in Week 3 to cover:
 * - override
 * - append_list
 * - fail_on_conflict
 * - nested maps
 * - empty layers/configs
 * - deeply nested maps
 */
class MergerTest {

    private final ClientSpec spec;

    MergerTest() throws Exception {
        spec = Loader.loadSpec(Path.of("config/client-spec.json"));
    }

    @Test
    void overlayPortWinsAndFeaturesAppend() throws Exception {
        ConfigDocument defaults = Loader.loadJson(Path.of("fixtures/defaults.json"));
        ConfigDocument overlay = Loader.loadJson(Path.of("fixtures/overlay.json"));
        MergeResult result = Merger.merge(List.of(defaults, overlay), spec);
        assertTrue(result.ok());
        @SuppressWarnings("unchecked")
        Map<String, Object> app = (Map<String, Object>) result.document().tree().get("app");
        assertEquals(9090, app.get("port"));
        assertEquals(List.of("metrics", "tracing"), app.get("features"));
    }

    @Test
    void regionConflictFails() throws Exception {
        ConfigDocument defaults = Loader.loadJson(Path.of("fixtures/defaults.json"));
        ConfigDocument overlay = Loader.loadJson(Path.of("fixtures/conflict-overlay.json"));
        MergeResult result = Merger.merge(List.of(defaults, overlay), spec);
        assertEquals(1, result.issues().size());
        assertEquals("app.region", result.issues().getFirst().path());
    }

    @Test
    void emptyLayersProduceEmptyDocument() {
        ClientSpec emptySpec = new ClientSpec(
                "1.0",
                "GenKey",
                List.of(),
                Map.of(),
                Map.of(),
                "override"
        );

        MergeResult result = Merger.merge(List.of(), emptySpec);
        assertTrue(result.document().tree().isEmpty());
        assertTrue(result.issues().isEmpty());
    }

    @Test
    void nestedMapsAreMerged() {
        ConfigDocument base = new ConfigDocument(Map.of(
                "app", Map.of(
                        "database", Map.of(
                                "host", "localhost"
                        )
                )
        ));

        ConfigDocument overlay = new ConfigDocument(Map.of(
                "app", Map.of(
                        "database", Map.of(
                                "port", 5432
                        )
                )
        ));

        ClientSpec nestedSpec = new ClientSpec(
                "1.0",
                "GenKey",
                List.of(),
                Map.of(),
                Map.of(),
                "override"
        );

        MergeResult result = Merger.merge(List.of(base, overlay), nestedSpec);
        @SuppressWarnings("unchecked")
        Map<String, Object> app = (Map<String, Object>) result.document().tree().get("app");
        @SuppressWarnings("unchecked")
        Map<String, Object> database = (Map<String, Object>) app.get("database");
        assertEquals("localhost", database.get("host"));
        assertEquals(5432, database.get("port"));
    }

    @Test
    void emptyConfigLayerDoesNotRemoveExistingValues() {
        ConfigDocument base = new ConfigDocument(Map.of(
                "app", Map.of(
                        "port", 8080
                )
        ));

        ConfigDocument emptyOverlay = new ConfigDocument(Map.of());

        ClientSpec emptySpec = new ClientSpec(
                "1.0",
                "GenKey",
                List.of(),
                Map.of(),
                Map.of(),
                "override"
        );

        MergeResult result = Merger.merge(List.of(base, emptyOverlay), emptySpec);
        @SuppressWarnings("unchecked")
        Map<String, Object> app = (Map<String, Object>) result.document().tree().get("app");
        assertEquals(8080, app.get("port"));
    }

    @Test
    void newFieldFromOverlayIsAdded() {
        ConfigDocument base = new ConfigDocument(Map.of(
                "app", Map.of(
                        "port", 8080
                )
        ));

        ConfigDocument overlay = new ConfigDocument(Map.of(
                "app", Map.of(
                        "region", "ghana"
                )
        ));

        ClientSpec addFieldSpec = new ClientSpec(
                "1.0",
                "GenKey",
                List.of(),
                Map.of(),
                Map.of(),
                "override"
        );

        MergeResult result = Merger.merge(List.of(base, overlay), addFieldSpec);
        @SuppressWarnings("unchecked")
        Map<String, Object> app = (Map<String, Object>) result.document().tree().get("app");
        assertEquals("ghana", app.get("region"));
    }

    @Test
    void appendListRequiresArrays() {
        ConfigDocument base = new ConfigDocument(Map.of(
                "app", Map.of(
                        "features", "metrics"
                )
        ));

        ConfigDocument overlay = new ConfigDocument(Map.of(
                "app", Map.of(
                        "features", "tracing"
                )
        ));

        ClientSpec appendSpec = new ClientSpec(
                "1.0",
                "GenKey",
                List.of(),
                Map.of(),
                Map.of("app.features", "append_list"),
                "override"
        );

        MergeResult result =
        Merger.merge(List.of(base, overlay), appendSpec);
        assertEquals(1, result.issues().size());
        assertEquals("append_list requires arrays on both sides", result.issues().getFirst().message());
    }

    @Test
    void deeplyNestedMapsAreMerged() {
        ConfigDocument base = new ConfigDocument(Map.of(
                "app", Map.of(
                        "database", Map.of(
                                "connection", Map.of(
                                        "host", "localhost"
                                )
                        )
                )
        ));

        ConfigDocument overlay = new ConfigDocument(Map.of(
                "app", Map.of(
                        "database", Map.of(
                                "connection", Map.of(
                                        "port", 5432
                                )
                        )
                )
        ));

        ClientSpec deepNestedSpec = new ClientSpec(
                "1.0",
                "GenKey",
                List.of(),
                Map.of(),
                Map.of(),
                "override"
        );

        MergeResult result = Merger.merge(List.of(base, overlay), deepNestedSpec);
        @SuppressWarnings("unchecked")
        Map<String, Object> app = (Map<String, Object>) result.document().tree().get("app");
        @SuppressWarnings("unchecked")
        Map<String, Object> database = (Map<String, Object>) app.get("database");
        @SuppressWarnings("unchecked")
        Map<String, Object> connection = (Map<String, Object>) database.get("connection");
        assertEquals("localhost", connection.get("host"));
        assertEquals(5432, connection.get("port"));
    }
}
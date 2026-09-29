package com.genkey.configmaster;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.Test;

import com.genkey.configmaster.model.ConfigDocument;
import com.genkey.configmaster.model.ValidationIssue;

class SchemaValidatorTest {

    @Test
    void missingRequiredFieldIsAnIssue() {
        ConfigDocument document = new ConfigDocument(Map.of(
                "app", Map.of(
                        "port", 8080
                )
        ));

        ClientSpec spec = new ClientSpec(
                "1.0",
                "GenKey",
                List.of("app.region"),
                Map.of(),
                Map.of(),
                "override"
        );

        List<ValidationIssue> issues =
                SchemaValidator.validate(document, spec);

        assertEquals(1, issues.size());
        assertEquals("app.region", issues.get(0).path());
        assertEquals(
                "required field is missing",
                issues.get(0).message()
        );
    }

    @Test
    void portMustBeInteger() {
        ConfigDocument document = new ConfigDocument(Map.of(
                "app", Map.of(
                        "port", "8080"
                )
        ));

        ClientSpec spec = new ClientSpec(
                "1.0",
                "GenKey",
                List.of(),
                Map.of("app.port", "integer"),
                Map.of(),
                "override"
        );

        List<ValidationIssue> issues =
                SchemaValidator.validate(document, spec);

        assertEquals(1, issues.size());
        assertEquals("app.port", issues.get(0).path());
        assertTrue(
                issues.get(0).message()
                        .contains("expected type integer")
        );
    }

    @Test
    void supportedTypesMatchCorrectly() {
        assertTrue(SchemaValidator.typeMatches("hello", "string"));
        assertTrue(SchemaValidator.typeMatches(10, "integer"));
        assertTrue(SchemaValidator.typeMatches(10L, "integer"));
        assertTrue(SchemaValidator.typeMatches(10.5, "number"));
        assertTrue(SchemaValidator.typeMatches(true, "boolean"));
        assertTrue(SchemaValidator.typeMatches(List.of("a", "b"), "array"));
        assertTrue(SchemaValidator.typeMatches(Map.of("key", "value"), "object"));
    }

    @Test
    void unknownTypeIsAccepted() {
        assertTrue(SchemaValidator.typeMatches("anything", "custom-type"));
    }

    @Test
    void missingTypedFieldIsIgnored() {
        ConfigDocument document = new ConfigDocument(Map.of());

        ClientSpec spec = new ClientSpec(
                "1.0",
                "GenKey",
                List.of(),
                Map.of("app.port", "integer"),
                Map.of(),
                "override"
    );

        List<ValidationIssue> issues =
                SchemaValidator.validate(document, spec);

    assertTrue(issues.isEmpty());
    }
}
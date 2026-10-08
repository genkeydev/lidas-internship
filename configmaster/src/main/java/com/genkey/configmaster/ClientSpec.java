package com.genkey.configmaster;

import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

/**
 * Machine-readable client needs. Loaded at runtime so a mentor can drop a
 * new brief + spec JSON without rewriting the engine.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public record ClientSpec(
        String schemaVersion,
        String client,
        List<String> requiredFields,
        Map<String, String> fieldTypes,
        Map<String, String> mergeStrategies,
        String defaultMergeStrategy
) {
    private static final Pattern SCHEMA_VERSION =
            Pattern.compile("^(\\d+)\\.(\\d+)\\.(\\d+)$");

    public String strategyFor(String dottedPath) {
        if (mergeStrategies != null && mergeStrategies.containsKey(dottedPath)) {
            return mergeStrategies.get(dottedPath);
        }
        return defaultMergeStrategy == null ? "override" : defaultMergeStrategy;
    }

    public void validateSchemaVersion() {
        if (schemaVersion == null || schemaVersion.isBlank()) {
            throw new IllegalArgumentException("schemaVersion is required");
        }

        Matcher matcher = SCHEMA_VERSION.matcher(schemaVersion);

        if (!matcher.matches()) {
            throw new IllegalArgumentException(
                    "invalid schemaVersion: " + schemaVersion);
        }

        if (!"1".equals(matcher.group(1))) {
            throw new IllegalArgumentException(
                    "unsupported schemaVersion: " + schemaVersion
                            + " (supported major version: 1)");
        }
    }
}

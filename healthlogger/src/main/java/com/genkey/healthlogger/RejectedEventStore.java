package com.genkey.healthlogger;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Stores rejected event submissions separately from valid events.
 *
 * Rejected submissions are written as JSON Lines to:
 * data/rejected-events.jsonl
 */
public final class RejectedEventStore {

    private final Path path;
    private final ObjectMapper mapper = Json.MAPPER;

    public RejectedEventStore(Path path) {
        this.path = path;
    }

    /**
     * Save a rejected submission.
     *
     * @param input  the original request body
     * @param reason the reason the submission was rejected
     */
    public void append(Object input, String reason) throws IOException {
        Files.createDirectories(path.getParent());

        Map<String, Object> rejection = new LinkedHashMap<>();
        rejection.put("timestamp", Instant.now().toString());
        rejection.put("input", input);
        rejection.put("reason", reason);

        String line = mapper.writeValueAsString(rejection)
                + System.lineSeparator();

        Files.writeString(
                path,
                line,
                StandardOpenOption.CREATE,
                StandardOpenOption.APPEND
        );
    }
}

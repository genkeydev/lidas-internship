package com.genkey.configmaster;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import com.genkey.configmaster.model.ConfigDocument;
import com.genkey.configmaster.model.MergeResult;
import com.genkey.configmaster.model.ValidationIssue;

/**
 * Command-line interface.
 *
 * <pre>
 *   validate  [--spec path] file.json [file.json ...]
 *   merge     [--spec path] file.json [file.json ...]
 *   show      [--spec path] file.json [file.json ...]
 * </pre>
 *
 * {@code CONFIGMASTER_SPEC} overrides the default {@code config/client-spec.json}.
 * Stdout is reserved for JSON; diagnostics go to stderr.
 */
public final class ConfigMasterCli {

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
            System.err.println("usage: configmaster validate|merge|show [--spec path] file.json ...");
            return 2;
        }
        String command = args[0];
        Path specPath = defaultSpec();
        List<Path> files = new ArrayList<>();
        for (int i = 1; i < args.length; i++) {
            if ("--spec".equals(args[i]) && i + 1 < args.length) {
                specPath = Path.of(args[++i]);
            } else {
                files.add(Path.of(args[i]));
            }
        }
        if (files.isEmpty()) {
            System.err.println("error: at least one JSON file is required");
            return 2;
        }

        ClientSpec spec = Loader.loadSpec(specPath);
        spec.validateSchemaVersion();

        List<ConfigDocument> layers = new ArrayList<>();
        for (Path file : files) {
            layers.add(Loader.loadJson(file));
        }
        System.err.println("loaded " + files.size() + " file(s); spec=" + specPath);

        MergeResult merged = Merger.merge(layers, spec);
        List<ValidationIssue> schemaIssues = SchemaValidator.validate(merged.document(), spec);
        List<ValidationIssue> all = new ArrayList<>(merged.issues());
        all.addAll(schemaIssues);

        return switch (command) {
            case "validate" -> {
                if (all.isEmpty()) {
                    System.err.println("valid");
                    yield 0;
                }
                printIssues(all);
                yield 1;
            }
            case "merge", "show" -> {
                if (!all.isEmpty()) {
                    printIssues(all);
                    yield 1;
                }
                System.out.println(Loader.toJson(merged.document().tree()));
                yield 0;
            }
            default -> {
                System.err.println("unknown command: " + command);
                yield 2;
            }
        };
    }

    private static Path defaultSpec() {
        String env = System.getenv("CONFIGMASTER_SPEC");
        if (env != null && !env.isBlank()) {
            return Path.of(env);
        }
        return Path.of("config/client-spec.json");
    }

    private static void printIssues(List<ValidationIssue> issues) {
        System.err.println(issues.size() + " issue(s):");
        for (ValidationIssue issue : issues) {
            System.err.println("  " + issue.path() + ": " + issue.message());
        }
    }
}

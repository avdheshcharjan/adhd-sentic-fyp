import os.log

/// Structured logging for ADHD Second Brain.
/// Uses Apple's unified logging system (os.log) for efficient, low-overhead logging.
enum Log {
    private static let subsystem = "com.adhdsecondrain.app"

    static let monitor = Logger(subsystem: subsystem, category: "monitor")
    static let network = Logger(subsystem: subsystem, category: "network")
    static let intervention = Logger(subsystem: subsystem, category: "intervention")
    static let permissions = Logger(subsystem: subsystem, category: "permissions")
    static let transition = Logger(subsystem: subsystem, category: "transition")
}

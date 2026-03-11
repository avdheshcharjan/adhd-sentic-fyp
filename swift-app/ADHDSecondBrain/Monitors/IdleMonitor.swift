import Foundation
import IOKit

/// Detects keyboard/mouse idle time using IOKit's HIDSystem.
/// No special permissions required.
///
/// Reports `isIdle = true` when there has been no input for > 60 seconds.
class IdleMonitor {

    // MARK: - Constants

    /// Seconds of no input before we consider the user idle.
    static let idleThresholdSeconds: TimeInterval = 60

    // MARK: - Public API

    /// Returns the number of seconds since the last keyboard or mouse input.
    static var idleTimeSeconds: TimeInterval {
        var iterator: io_iterator_t = 0
        defer { IOObjectRelease(iterator) }

        guard IOServiceGetMatchingServices(
            kIOMainPortDefault,
            IOServiceMatching("IOHIDSystem"),
            &iterator
        ) == KERN_SUCCESS else {
            return 0
        }

        let entry = IOIteratorNext(iterator)
        defer { IOObjectRelease(entry) }
        guard entry != 0 else { return 0 }

        var unmanagedDict: Unmanaged<CFMutableDictionary>?
        guard IORegistryEntryCreateCFProperties(
            entry,
            &unmanagedDict,
            kCFAllocatorDefault,
            0
        ) == KERN_SUCCESS,
              let dict = unmanagedDict?.takeRetainedValue() as NSDictionary?
        else {
            return 0
        }

        guard let idleTime = dict["HIDIdleTime"] as? Int64 else {
            return 0
        }

        // HIDIdleTime is in nanoseconds — convert to seconds
        return TimeInterval(idleTime) / 1_000_000_000
    }

    /// Returns true if the user has been idle longer than the threshold (60s).
    static var isIdle: Bool {
        return idleTimeSeconds >= idleThresholdSeconds
    }
}

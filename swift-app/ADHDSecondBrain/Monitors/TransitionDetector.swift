import Foundation

/// Detects natural task breakpoints for intervention delivery.
///
/// Based on Iqbal & Bailey (CHI 2008): delivering notifications at coarse
/// breakpoints reduces frustration and resumption lag.
///
/// RULES:
/// - Interventions are ONLY delivered at detected breakpoints
/// - If no breakpoint occurs within 5 minutes of trigger, downgrade to Tier 1 (ambient)
/// - NEVER interrupt during sustained single-app focus (anti-pattern #4)
class TransitionDetector: ObservableObject {

    // MARK: - Types

    enum BreakpointType: String {
        case appSwitch = "app_switch"
        case tabBurst = "tab_burst"           // 3+ tab switches in 30 seconds
        case idleResume = "idle_resume"
        case distractionEntry = "distraction_entry"
    }

    struct TransitionEvent {
        let type: String
        let from: String?
        let to: String?
        let timestamp: Date
    }

    // MARK: - Published State

    @Published private(set) var isAtBreakpoint: Bool = false
    @Published private(set) var lastBreakpointType: BreakpointType?

    // MARK: - Private State

    private var recentEvents: [TransitionEvent] = []
    private let maxEvents = 100

    private var currentApp: String = ""
    private var currentAppSince: Date = Date()
    private var lastBreakpointTime: Date?

    /// How long a breakpoint is "fresh" after detection (seconds)
    private let breakpointFreshnessWindow: TimeInterval = 10.0

    /// Deep focus threshold — never interrupt after this duration
    private let deepFocusThreshold: TimeInterval = 900 // 15 minutes

    // MARK: - Public API

    /// Record an application switch event.
    func recordAppSwitch(from: String, to: String, timestamp: Date = Date()) {
        addEvent(TransitionEvent(type: "app_switch", from: from, to: to, timestamp: timestamp))

        currentApp = to
        currentAppSince = timestamp
        markBreakpoint(type: .appSwitch, at: timestamp)
    }

    /// Record a browser tab switch.
    func recordTabSwitch(urlOrTitle: String, timestamp: Date = Date()) {
        addEvent(TransitionEvent(type: "tab_switch", from: nil, to: urlOrTitle, timestamp: timestamp))

        // Check for tab burst: 3+ tab switches in 30 seconds
        let recent = recentEvents.filter {
            $0.type == "tab_switch" && timestamp.timeIntervalSince($0.timestamp) < 30
        }
        if recent.count >= 3 {
            markBreakpoint(type: .tabBurst, at: timestamp)
        }
    }

    /// Record return from idle (user came back after 30+ seconds of inactivity).
    func recordIdleResume(timestamp: Date = Date()) {
        addEvent(TransitionEvent(type: "idle_end", from: nil, to: nil, timestamp: timestamp))
        markBreakpoint(type: .idleResume, at: timestamp)
    }

    /// Record start of idle period.
    func recordIdleStart(timestamp: Date = Date()) {
        addEvent(TransitionEvent(type: "idle_start", from: nil, to: nil, timestamp: timestamp))
    }

    /// Check if the user is currently at a natural task boundary.
    /// Called by TierManager before delivering any intervention.
    func checkBreakpoint() -> Bool {
        guard let last = lastBreakpointTime else { return false }
        let fresh = Date().timeIntervalSince(last) < breakpointFreshnessWindow
        isAtBreakpoint = fresh
        return fresh
    }

    /// Returns true if the user is in deep focus and should NOT be interrupted.
    /// This is the HARD BLOCK — no intervention of any tier passes through.
    /// Anti-pattern #4: NEVER interrupt productive hyperfocus.
    func shouldSuppressIntervention() -> Bool {
        let focusSeconds = Date().timeIntervalSince(currentAppSince)
        return focusSeconds > deepFocusThreshold
    }

    /// How long the user has been on the current app without switching.
    var focusDurationSeconds: TimeInterval {
        return Date().timeIntervalSince(currentAppSince)
    }

    // MARK: - Private

    private func addEvent(_ event: TransitionEvent) {
        recentEvents.append(event)
        if recentEvents.count > maxEvents {
            recentEvents.removeFirst(recentEvents.count - maxEvents)
        }
    }

    private func markBreakpoint(type: BreakpointType, at time: Date) {
        lastBreakpointTime = time
        lastBreakpointType = type
        isAtBreakpoint = true
    }
}

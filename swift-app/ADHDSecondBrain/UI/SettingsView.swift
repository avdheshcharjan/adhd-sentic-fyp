import SwiftUI
import UserNotifications

// MARK: - Settings Tab Enum

enum SettingsTab: String, CaseIterable, Identifiable {
    case general      = "General"
    case permissions  = "Permissions"
    case focusSessions = "Focus Sessions"
    case shortcuts    = "Shortcuts"
    case whoop        = "Whoop"
    case notifications = "Notifications"
    case about        = "About"

    var id: String { rawValue }
}

// MARK: - Root Settings View

/// Two-panel settings window matching Paper canvas design.
/// 680px wide, minimum 440px tall.
/// Left sidebar (180px) + right content area.
struct SettingsView: View {

    @State private var selectedTab: SettingsTab = .general

    var body: some View {
        HStack(spacing: 0) {
            SettingsSidebar(selectedTab: $selectedTab)
                .frame(width: 180)

            Divider()
                .overlay(Color.white.opacity(0.06))

            SettingsContentArea(selectedTab: selectedTab)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .frame(width: 680)
        .frame(minHeight: 440)
        .background(ADHDColors.Background.primary)
    }
}

// MARK: - Left Sidebar

private struct SettingsSidebar: View {
    @Binding var selectedTab: SettingsTab

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            ForEach(SettingsTab.allCases) { tab in
                SidebarNavItem(
                    title: tab.rawValue,
                    isSelected: selectedTab == tab
                ) {
                    selectedTab = tab
                }
            }
            Spacer()
        }
        .padding(12)
        .frame(maxHeight: .infinity)
        .background(ADHDColors.Background.elevated)
    }
}

// MARK: - Sidebar Nav Item

private struct SidebarNavItem: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(
                    isSelected
                        ? Font.custom("Lexend-Medium", size: 13)
                        : Font.custom("Lexend-Regular", size: 13)
                )
                .foregroundColor(
                    isSelected
                        ? ADHDColors.Accent.focusLight
                        : ADHDColors.Text.secondary
                )
                .frame(width: 156, alignment: .leading)
                .padding(.vertical, 8)
                .padding(.horizontal, 12)
                .background(
                    isSelected
                        ? ADHDColors.Accent.focusLight.opacity(0.08)
                        : Color.clear
                )
                .cornerRadius(10)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Right Content Area (tab router)

private struct SettingsContentArea: View {
    let selectedTab: SettingsTab

    var body: some View {
        ScrollView(.vertical, showsIndicators: false) {
            switch selectedTab {
            case .general:
                GeneralSettingsPage()
            case .permissions:
                PermissionsSettingsPage()
            case .focusSessions:
                FocusSessionsSettingsPage()
            case .shortcuts:
                ModalSettingsView()
            case .whoop:
                WhoopSettingsPage()
            case .notifications:
                NotificationsSettingsPage()
            case .about:
                AboutSettingsPage()
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - General Settings Page

private struct GeneralSettingsPage: View {

    @AppStorage("launchAtLogin")     private var launchAtLogin: Bool   = true
    @AppStorage("notchWidget")       private var notchWidget: Bool      = true
    @AppStorage("reducedMotion")     private var reducedMotion: Bool    = false
    @AppStorage("defaultFocusBlock") private var defaultFocusBlock: Int = 45
    @AppStorage("backendURL")        private var backendURL: String     = "localhost:8420"

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("General")
                .font(Font.custom("Lexend-SemiBold", size: 18))
                .foregroundColor(ADHDColors.Text.primary)
                .padding(.bottom, 24)

            VStack(spacing: 24) {
                SettingsToggleRow(
                    label: "Launch at login",
                    description: "Start monitoring when you log in",
                    isOn: $launchAtLogin
                )

                SettingsToggleRow(
                    label: "Notch widget",
                    description: "Show the Dynamic Island overlay",
                    isOn: $notchWidget
                )

                SettingsToggleRow(
                    label: "Reduced motion",
                    description: "Minimize animations and transitions",
                    isOn: $reducedMotion
                )

                SettingsValuePillRow(
                    label: "Default focus block",
                    description: "Duration before a break is suggested",
                    valueText: "\(defaultFocusBlock) min"
                )

                SettingsURLRow(
                    label: "Backend URL",
                    description: "API endpoint for the Python backend",
                    value: $backendURL
                )

                SettingsGoogleCalendarRow()
            }
        }
        .padding(.vertical, 24)
        .padding(.horizontal, 28)
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }
}

// MARK: - Permissions Settings Page

private struct PermissionsSettingsPage: View {

    @State private var hasAccessibility: Bool = false
    @State private var hasAutomation: Bool = false
    @State private var notificationStatus: UNAuthorizationStatus = .notDetermined
    @State private var pollingTimer: Timer? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("Permissions")
                .font(Font.custom("Lexend-SemiBold", size: 18))
                .foregroundColor(ADHDColors.Text.primary)
                .padding(.bottom, 24)

            VStack(spacing: 20) {
                // Accessibility row
                HStack(alignment: .center) {
                    SettingsRowLabel(
                        label: "Accessibility",
                        description: "Required for window title reading via AXUIElement"
                    )
                    Spacer()
                    if hasAccessibility {
                        PermissionGrantedBadge()
                    } else {
                        PermissionGrantButton(title: "Grant Access") {
                            Permissions.requestAccessibility()
                        }
                    }
                }

                // Automation row
                HStack(alignment: .center) {
                    SettingsRowLabel(
                        label: "Automation",
                        description: "AppleScript access for browser URL extraction"
                    )
                    Spacer()
                    if hasAutomation {
                        PermissionGrantedBadge()
                    } else {
                        PermissionGrantButton(title: "Grant Access") {
                            Permissions.requestAutomation()
                        }
                    }
                }

                // Notifications row
                HStack(alignment: .center) {
                    SettingsRowLabel(
                        label: "Notifications",
                        description: "Alerts and sounds for Tier 4-5 interventions"
                    )
                    Spacer()
                    if notificationStatus == .authorized {
                        PermissionGrantedBadge()
                    } else {
                        PermissionGrantButton(title: "Grant Access") {
                            openNotificationSettings()
                        }
                    }
                }

                // Note text
                Text("Screen Recording is not required. Window titles are read via Accessibility APIs without capturing screen content.")
                    .font(Font.custom("Lexend-Regular", size: 12))
                    .foregroundColor(ADHDColors.Text.muted)
                    .fixedSize(horizontal: false, vertical: true)
                    .padding(.top, 4)

                // Open System Settings button
                Button {
                    Permissions.openPrivacySettings()
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: "info.circle")
                            .font(.system(size: 13))
                            .foregroundColor(ADHDColors.Accent.focusLight)
                        Text("Open System Settings")
                            .font(Font.custom("Lexend-Medium", size: 13))
                            .foregroundColor(ADHDColors.Accent.focusLight)
                    }
                    .padding(.vertical, 8)
                    .padding(.horizontal, 14)
                    .background(ADHDColors.Accent.focusLight.opacity(0.1))
                    .cornerRadius(10)
                }
                .buttonStyle(.plain)
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .padding(.vertical, 24)
        .padding(.horizontal, 28)
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .onAppear {
            refreshPermissionsAsync()
            Task { await fetchNotificationStatus() }
            startPolling()
        }
        .onDisappear {
            pollingTimer?.invalidate()
            pollingTimer = nil
        }
    }

    /// Runs permission checks on a background thread — `hasAutomation` does
    /// blocking NSAppleScript IPC and must not run on main.
    private func refreshPermissionsAsync() {
        Task.detached(priority: .utility) {
            let accessibility = Permissions.hasAccessibility
            let automation = Permissions.hasAutomation
            await MainActor.run {
                hasAccessibility = accessibility
                hasAutomation = automation
            }
        }
    }

    private func fetchNotificationStatus() async {
        let settings = await UNUserNotificationCenter.current().notificationSettings()
        notificationStatus = settings.authorizationStatus
    }

    private func openNotificationSettings() {
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.notifications") {
            NSWorkspace.shared.open(url)
        }
    }

    private func startPolling() {
        pollingTimer?.invalidate()
        pollingTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { _ in
            refreshPermissionsAsync()
            Task { await fetchNotificationStatus() }
        }
    }
}

// MARK: - Permissions Helper Views

private struct PermissionGrantedBadge: View {
    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(ADHDColors.Accent.success)
                .frame(width: 8, height: 8)
            Text("Granted")
                .font(Font.custom("Lexend-Medium", size: 13))
                .foregroundColor(ADHDColors.Accent.success)
        }
        .padding(.vertical, 6)
        .padding(.horizontal, 14)
        .background(ADHDColors.Accent.success.opacity(0.1))
        .cornerRadius(10)
    }
}

private struct PermissionGrantButton: View {
    let title: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(Font.custom("Lexend-Medium", size: 13))
                .foregroundColor(ADHDColors.Accent.focusLight)
                .padding(.vertical, 6)
                .padding(.horizontal, 14)
                .background(ADHDColors.Accent.focusLight.opacity(0.1))
                .cornerRadius(10)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Focus Sessions Settings Page

private struct FocusSessionsSettingsPage: View {

    @AppStorage("defaultFocusBlock")       private var defaultFocusBlock: Int       = 45
    @AppStorage("breakReminders")          private var breakReminders: Bool          = true
    @AppStorage("autoDetectSessions")      private var autoDetectSessions: Bool      = true
    @AppStorage("hyperfocusProtection")    private var hyperfocusProtection: Bool    = false
    @AppStorage("maxInterventionsPerBlock") private var maxInterventionsPerBlock: Int = 3
    @AppStorage("offTaskAlerts")            private var offTaskAlerts: Bool            = true
    @AppStorage("offTaskAlertsAlways")      private var offTaskAlertsAlways: Bool      = false

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("Focus Sessions")
                .font(Font.custom("Lexend-SemiBold", size: 18))
                .foregroundColor(ADHDColors.Text.primary)
                .padding(.bottom, 24)

            VStack(spacing: 24) {
                // Default focus block stepper row
                SettingsStepperRow(
                    label: "Default focus block",
                    description: "Duration before a break is suggested",
                    value: $defaultFocusBlock,
                    step: 5,
                    range: 15...90,
                    unit: "min"
                )

                SettingsToggleRow(
                    label: "Break reminders",
                    description: "Gentle nudge when a focus block ends",
                    isOn: $breakReminders
                )

                SettingsToggleRow(
                    label: "Auto-detect sessions",
                    description: "Start focus blocks automatically from activity patterns",
                    isOn: $autoDetectSessions
                )

                SettingsToggleRow(
                    label: "Hyperfocus protection",
                    description: "Intervene when hyperfocus exceeds 90 minutes",
                    isOn: $hyperfocusProtection
                )

                SettingsValuePillRow(
                    label: "Max interventions per block",
                    description: "Limit nudges within a 90-minute window",
                    valueText: "\(maxInterventionsPerBlock)"
                )

                SettingsToggleRow(
                    label: "Off-task alerts",
                    description: "Blink the notch red when you drift to irrelevant apps during focus",
                    isOn: $offTaskAlerts
                )

                SettingsToggleRow(
                    label: "Alert even without active task",
                    description: "Flag high-suspicion categories even when no focus task is running",
                    isOn: $offTaskAlertsAlways
                )
                .disabled(!offTaskAlerts)
                .opacity(offTaskAlerts ? 1.0 : 0.5)
            }
        }
        .padding(.vertical, 24)
        .padding(.horizontal, 28)
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }
}

// MARK: - Stepper Row Component

private struct SettingsStepperRow: View {
    let label: String
    let description: String
    @Binding var value: Int
    let step: Int
    let range: ClosedRange<Int>
    let unit: String

    var body: some View {
        HStack(alignment: .center) {
            SettingsRowLabel(label: label, description: description)
            Spacer()
            HStack(spacing: 6) {
                // Minus button
                Button {
                    let newValue = value - step
                    if newValue >= range.lowerBound {
                        value = newValue
                    }
                } label: {
                    Image(systemName: "minus")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(
                            value > range.lowerBound
                                ? ADHDColors.Text.secondary
                                : ADHDColors.Text.muted
                        )
                        .frame(width: 28, height: 28)
                        .background(ADHDColors.Background.secondary)
                        .cornerRadius(8)
                }
                .buttonStyle(.plain)
                .disabled(value <= range.lowerBound)

                // Value pill
                Text("\(value) \(unit)")
                    .font(Font.custom("Lexend-Medium", size: 14).monospacedDigit())
                    .foregroundColor(ADHDColors.Text.primary)
                    .padding(.vertical, 6)
                    .padding(.horizontal, 14)
                    .background(ADHDColors.Background.secondary)
                    .cornerRadius(10)
                    .frame(minWidth: 72)

                // Plus button
                Button {
                    let newValue = value + step
                    if newValue <= range.upperBound {
                        value = newValue
                    }
                } label: {
                    Image(systemName: "plus")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(
                            value < range.upperBound
                                ? ADHDColors.Text.secondary
                                : ADHDColors.Text.muted
                        )
                        .frame(width: 28, height: 28)
                        .background(ADHDColors.Background.secondary)
                        .cornerRadius(8)
                }
                .buttonStyle(.plain)
                .disabled(value >= range.upperBound)
            }
        }
    }
}

// MARK: - Whoop Settings Page

private struct WhoopSettingsPage: View {

    @AppStorage("adaptiveFocusBlocks") private var adaptiveFocusBlocks: Bool = true
    @AppStorage("morningBriefing")     private var morningBriefing: Bool     = true
    @AppStorage("backendURL")          private var backendURL: String        = "localhost:8420"

    @State private var isConnected: Bool = false
    @State private var lastSyncTime: Date? = nil
    @State private var isCheckingStatus: Bool = false
    let timer = Timer.publish(every: 3, on: .main, in: .common).autoconnect()

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("Whoop")
                .font(Font.custom("Lexend-SemiBold", size: 18))
                .foregroundColor(ADHDColors.Text.primary)
                .padding(.bottom, 24)

            VStack(spacing: 24) {
                // Connection status card
                WhoopConnectionCard(
                    isConnected: isConnected,
                    lastSyncTime: lastSyncTime,
                    onConnect: { [backendURL] in
                        guard let url = URL(string: "http://\(backendURL)/api/auth/whoop") else { return }
                        NSWorkspace.shared.open(url)
                    },
                    onDisconnect: {
                        Task { await disconnectWhoop() }
                    }
                )

                SettingsToggleRow(
                    label: "Adaptive focus blocks",
                    description: "Adjust block duration based on recovery score",
                    isOn: $adaptiveFocusBlocks
                )

                SettingsToggleRow(
                    label: "Morning briefing",
                    description: "AI summary from sleep and recovery data",
                    isOn: $morningBriefing
                )

                HStack(alignment: .center) {
                    SettingsRowLabel(
                        label: "Sync interval",
                        description: "How often biometric data is fetched"
                    )
                    Spacer()
                    SettingsValuePill(text: "30s")
                }
            }
        }
        .padding(.vertical, 24)
        .padding(.horizontal, 28)
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .task {
            await checkWhoopStatus()
        }
        .onReceive(timer) { _ in
            Task { await checkWhoopStatus() }
        }
    }

    private func checkWhoopStatus() async {
        guard !isCheckingStatus else { return }
        isCheckingStatus = true
        defer { isCheckingStatus = false }

        guard let url = URL(string: "http://\(backendURL)/api/auth/whoop/status") else { return }
        do {
            let config = URLSessionConfiguration.default
            config.timeoutIntervalForRequest = 5
            let session = URLSession(configuration: config)
            let (data, response) = try await session.data(from: url)
            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else { return }
            struct WhoopStatus: Decodable {
                let connected: Bool
            }
            let status = try JSONDecoder().decode(WhoopStatus.self, from: data)
            isConnected = status.connected
            if status.connected {
                lastSyncTime = Date()
            }
        } catch {
            // Backend not reachable — leave isConnected as false
        }
    }

    private func disconnectWhoop() async {
        guard let url = URL(string: "http://\(backendURL)/api/auth/whoop/disconnect") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        do {
            let config = URLSessionConfiguration.default
            config.timeoutIntervalForRequest = 5
            let session = URLSession(configuration: config)
            let (_, _) = try await session.data(for: request)
            isConnected = false
            lastSyncTime = nil
        } catch {
            // Ignore — treat as success (token cleared client-side)
            isConnected = false
            lastSyncTime = nil
        }
    }
}

private struct WhoopConnectionCard: View {
    let isConnected: Bool
    let lastSyncTime: Date?
    let onConnect: () -> Void
    let onDisconnect: () -> Void

    private var relativeTimeString: String {
        guard let date = lastSyncTime else { return "Never synced" }
        let elapsed = Date().timeIntervalSince(date)
        if elapsed < 60 {
            return "Last synced just now"
        } else if elapsed < 3600 {
            let minutes = Int(elapsed / 60)
            return "Last synced \(minutes) minute\(minutes == 1 ? "" : "s") ago"
        } else {
            let hours = Int(elapsed / 3600)
            return "Last synced \(hours) hour\(hours == 1 ? "" : "s") ago"
        }
    }

    var body: some View {
        HStack(spacing: 14) {
            // Icon
            ZStack {
                RoundedRectangle(cornerRadius: 10)
                    .fill(
                        isConnected
                            ? ADHDColors.Accent.success.opacity(0.15)
                            : ADHDColors.Background.primary
                    )
                    .frame(width: 36, height: 36)
                Image(systemName: isConnected ? "checkmark" : "xmark")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(
                        isConnected
                            ? ADHDColors.Accent.success
                            : ADHDColors.Text.tertiary
                    )
            }

            // Text
            VStack(alignment: .leading, spacing: 2) {
                Text(isConnected ? "Whoop 4.0 Connected" : "Not Connected")
                    .font(Font.custom("Lexend-Medium", size: 14))
                    .foregroundColor(ADHDColors.Text.primary)
                Text(isConnected ? relativeTimeString : "Connect your Whoop device")
                    .font(Font.custom("Lexend-Regular", size: 12))
                    .foregroundColor(ADHDColors.Text.tertiary)
            }

            Spacer()

            // Action button
            if isConnected {
                Button(action: onDisconnect) {
                    Text("Disconnect")
                        .font(Font.custom("Lexend-Medium", size: 13))
                        .foregroundColor(ADHDColors.Accent.danger)
                        .padding(.vertical, 6)
                        .padding(.horizontal, 14)
                        .background(ADHDColors.Accent.danger.opacity(0.1))
                        .cornerRadius(10)
                }
                .buttonStyle(.plain)
            } else {
                Button(action: onConnect) {
                    Text("Connect")
                        .font(Font.custom("Lexend-Medium", size: 13))
                        .foregroundColor(ADHDColors.Accent.focusLight)
                        .padding(.vertical, 6)
                        .padding(.horizontal, 14)
                        .background(ADHDColors.Accent.focusLight.opacity(0.1))
                        .cornerRadius(10)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(14)
        .background(ADHDColors.Background.elevated)
        .cornerRadius(12)
    }
}

// MARK: - Notifications Settings Page

private struct NotificationsSettingsPage: View {

    @AppStorage("tier1Enabled")         private var tier1Enabled: Bool         = true
    @AppStorage("tier2Enabled")         private var tier2Enabled: Bool         = true
    @AppStorage("tier3Enabled")         private var tier3Enabled: Bool         = true
    @AppStorage("tier4Enabled")         private var tier4Enabled: Bool         = true
    @AppStorage("notificationSounds")   private var notificationSounds: Bool   = true

    private struct TierInfo {
        let number: Int
        let label: String
        let description: String
    }

    private let tiers: [TierInfo] = [
        TierInfo(number: 1, label: "Ambient color shift",  description: "Passive menu bar icon tint"),
        TierInfo(number: 2, label: "Gentle pulse",         description: "Subtle animation on menu bar icon"),
        TierInfo(number: 3, label: "Calm overlay",         description: "Non-activating overlay panel with suggestion"),
        TierInfo(number: 4, label: "System toast",         description: "macOS notification with sound"),
        TierInfo(number: 5, label: "Full alert",           description: "Notification + overlay — safety-critical only"),
    ]

    private func tierBadgeBackground(for tier: Int) -> Color {
        switch tier {
        case 1: return ADHDColors.Accent.focus.opacity(0.15)
        case 2: return ADHDColors.Accent.focus.opacity(0.25)
        case 3: return ADHDColors.Accent.warmth.opacity(0.15)
        case 4: return ADHDColors.Accent.alert.opacity(0.15)
        case 5: return ADHDColors.Accent.danger.opacity(0.15)
        default: return ADHDColors.Background.secondary
        }
    }

    private func tierBadgeForeground(for tier: Int) -> Color {
        switch tier {
        case 1, 2: return ADHDColors.Accent.focusLight
        case 3:    return ADHDColors.Accent.warmth
        case 4:    return ADHDColors.Accent.alert
        case 5:    return ADHDColors.Accent.danger
        default:   return ADHDColors.Text.secondary
        }
    }

    private func tierBinding(for tier: Int) -> Binding<Bool> {
        switch tier {
        case 1: return $tier1Enabled
        case 2: return $tier2Enabled
        case 3: return $tier3Enabled
        case 4: return $tier4Enabled
        default: return .constant(true)
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("Notifications")
                .font(Font.custom("Lexend-SemiBold", size: 18))
                .foregroundColor(ADHDColors.Text.primary)
                .padding(.bottom, 20)

            // Section header
            Text("INTERVENTION TIERS")
                .font(Font.custom("Lexend-Medium", size: 11))
                .foregroundColor(ADHDColors.Text.tertiary)
                .tracking(0.05 * 11)
                .padding(.bottom, 12)

            VStack(spacing: 16) {
                ForEach(tiers, id: \.number) { tier in
                    HStack(alignment: .center, spacing: 12) {
                        // Numbered badge
                        ZStack {
                            RoundedRectangle(cornerRadius: 7)
                                .fill(tierBadgeBackground(for: tier.number))
                                .frame(width: 24, height: 24)
                            Text("\(tier.number)")
                                .font(Font.custom("Lexend-SemiBold", size: 12))
                                .foregroundColor(tierBadgeForeground(for: tier.number))
                        }

                        // Label + description
                        VStack(alignment: .leading, spacing: 2) {
                            Text(tier.label)
                                .font(Font.custom("Lexend-Medium", size: 14))
                                .foregroundColor(ADHDColors.Text.primary)
                            Text(tier.description)
                                .font(Font.custom("Lexend-Regular", size: 12))
                                .foregroundColor(ADHDColors.Text.tertiary)
                        }

                        Spacer()

                        // Right control
                        if tier.number == 5 {
                            // Always on badge — safety critical, non-toggleable
                            Text("Always on")
                                .font(Font.custom("Lexend-Medium", size: 12))
                                .foregroundColor(ADHDColors.Accent.danger)
                                .padding(.vertical, 4)
                                .padding(.horizontal, 10)
                                .background(ADHDColors.Accent.danger.opacity(0.12))
                                .cornerRadius(8)
                        } else {
                            SettingsToggle(isOn: tierBinding(for: tier.number))
                        }
                    }
                }
            }

            // Separator
            Rectangle()
                .fill(Color.white.opacity(0.06))
                .frame(height: 1)
                .padding(.vertical, 20)

            // Notification sounds toggle
            SettingsToggleRow(
                label: "Notification sounds",
                description: "Play a sound with Tier 4-5 alerts",
                isOn: $notificationSounds
            )
        }
        .padding(.vertical, 24)
        .padding(.horizontal, 28)
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }
}

// MARK: - About Settings Page

private struct AboutSettingsPage: View {

    private var appVersion: String {
        let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
        let build   = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1"
        return "Version \(version) (Build \(build))"
    }

    private struct TechBadge {
        let label: String
        let background: Color
        let foreground: Color
    }

    private let techBadges: [TechBadge] = [
        TechBadge(
            label: "SenticNet",
            background: ADHDColors.Accent.focus.opacity(0.12),
            foreground: ADHDColors.Accent.focusLight
        ),
        TechBadge(
            label: "MLX",
            background: ADHDColors.Accent.success.opacity(0.12),
            foreground: ADHDColors.Accent.success
        ),
        TechBadge(
            label: "Mem0",
            background: ADHDColors.Accent.warmth.opacity(0.12),
            foreground: ADHDColors.Accent.warmth
        ),
        TechBadge(
            label: "Whoop",
            background: ADHDColors.Text.secondary.opacity(0.10),
            foreground: ADHDColors.Text.secondary
        ),
    ]

    private struct AboutLink {
        let label: String
        let url: String
    }

    private let links: [AboutLink] = [
        AboutLink(label: "GitHub",        url: "https://github.com/avdheshcharjan/adhd-sentic-fyp"),
        AboutLink(label: "Documentation", url: "https://github.com/avdheshcharjan/adhd-sentic-fyp/wiki"),
        AboutLink(label: "Report Issue",  url: "https://github.com/avdheshcharjan/adhd-sentic-fyp/issues"),
    ]

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            VStack(spacing: 16) {
                // App icon
                ZStack {
                    RoundedRectangle(cornerRadius: 16)
                        .fill(
                            LinearGradient(
                                colors: [ADHDColors.Accent.focus, ADHDColors.Accent.focusLight],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 64, height: 64)

                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 28, weight: .medium))
                        .foregroundColor(.white)
                }

                // App name + version
                VStack(spacing: 4) {
                    Text("ADHD Second Brain")
                        .font(Font.custom("Lexend-SemiBold", size: 18))
                        .foregroundColor(ADHDColors.Text.primary)

                    Text(appVersion)
                        .font(Font.custom("Lexend-Regular", size: 13))
                        .foregroundColor(ADHDColors.Text.tertiary)

                    Text("Always-on ADHD support powered by affective computing")
                        .font(Font.custom("Lexend-Regular", size: 12))
                        .foregroundColor(ADHDColors.Text.secondary)
                        .multilineTextAlignment(.center)
                }

                // Tech stack badges
                HStack(spacing: 8) {
                    ForEach(techBadges, id: \.label) { badge in
                        Text(badge.label)
                            .font(Font.custom("Lexend-Medium", size: 12))
                            .foregroundColor(badge.foreground)
                            .padding(.vertical, 5)
                            .padding(.horizontal, 12)
                            .background(badge.background)
                            .cornerRadius(8)
                    }
                }

                // Links row
                HStack(spacing: 0) {
                    ForEach(Array(links.enumerated()), id: \.offset) { index, link in
                        if index > 0 {
                            Rectangle()
                                .fill(Color.white.opacity(0.15))
                                .frame(width: 1, height: 14)
                                .padding(.horizontal, 10)
                        }
                        Button {
                            guard let url = URL(string: link.url) else { return }
                            NSWorkspace.shared.open(url)
                        } label: {
                            Text(link.label)
                                .font(Font.custom("Lexend-Medium", size: 13))
                                .foregroundColor(ADHDColors.Accent.focusLight)
                        }
                        .buttonStyle(.plain)
                    }
                }

                // Footer
                VStack(spacing: 2) {
                    Text("Final Year Project — Nanyang Technological University")
                        .font(Font.custom("Lexend-Regular", size: 11))
                        .foregroundColor(ADHDColors.Text.muted)

                    Text("2025-2026 Avdhesh Charjan")
                        .font(Font.custom("Lexend-Regular", size: 11))
                        .foregroundColor(ADHDColors.Text.muted)
                }
                .multilineTextAlignment(.center)
            }

            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(.horizontal, 28)
    }
}

// MARK: - Reusable Settings Row Components

/// A row with a label/description on the left and a toggle on the right.
private struct SettingsToggleRow: View {
    let label: String
    let description: String
    @Binding var isOn: Bool

    var body: some View {
        HStack(alignment: .center) {
            SettingsRowLabel(label: label, description: description)
            Spacer()
            SettingsToggle(isOn: $isOn)
        }
    }
}

/// A row with a label/description on the left and a static value pill on the right.
private struct SettingsValuePillRow: View {
    let label: String
    let description: String
    let valueText: String

    var body: some View {
        HStack(alignment: .center) {
            SettingsRowLabel(label: label, description: description)
            Spacer()
            SettingsValuePill(text: valueText)
        }
    }
}

/// A row for the backend URL — shows the URL in a pill with muted styling.
private struct SettingsURLRow: View {
    let label: String
    let description: String
    @Binding var value: String

    var body: some View {
        HStack(alignment: .center) {
            SettingsRowLabel(label: label, description: description)
            Spacer()
            Text(value)
                .font(Font.custom("Lexend-Regular", size: 13))
                .foregroundColor(ADHDColors.Text.secondary)
                .padding(.vertical, 6)
                .padding(.horizontal, 14)
                .background(ADHDColors.Background.secondary)
                .cornerRadius(10)
        }
    }
}

/// Left-side label + description stack used in all setting rows.
private struct SettingsRowLabel: View {
    let label: String
    let description: String

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label)
                .font(Font.custom("Lexend-Medium", size: 14))
                .foregroundColor(ADHDColors.Text.primary)
            Text(description)
                .font(Font.custom("Lexend-Regular", size: 12))
                .foregroundColor(ADHDColors.Text.tertiary)
        }
    }
}

/// 44x24 pill toggle. on = green (0x28C840), off = muted (0x47474D).
private struct SettingsToggle: View {
    @Binding var isOn: Bool

    private let width: CGFloat  = 44
    private let height: CGFloat = 24
    private let knobSize: CGFloat = 20

    var body: some View {
        ZStack {
            Capsule()
                .fill(isOn ? ADHDColors.Accent.successBright : ADHDColors.Text.muted)
                .frame(width: width, height: height)

            Circle()
                .fill(Color.white)
                .frame(width: knobSize, height: knobSize)
                .offset(x: isOn ? (width / 2 - knobSize / 2 - 2) : -(width / 2 - knobSize / 2 - 2))
                .animation(.spring(response: 0.25, dampingFraction: 0.75), value: isOn)
        }
        .frame(width: width, height: height)
        .contentShape(Rectangle())
        .onTapGesture { isOn.toggle() }
    }
}

/// Static value pill — dark background, primary text, tabular digits.
private struct SettingsValuePill: View {
    let text: String

    var body: some View {
        Text(text)
            .font(
                Font.custom("Lexend-Medium", size: 14)
                    .monospacedDigit()
            )
            .foregroundColor(ADHDColors.Text.primary)
            .padding(.vertical, 6)
            .padding(.horizontal, 14)
            .background(ADHDColors.Background.secondary)
            .cornerRadius(10)
    }
}

// MARK: - Google Calendar Connection Row

private struct SettingsGoogleCalendarRow: View {
    @AppStorage("backendURL") private var backendURL: String = "localhost:8420"
    @State private var isConnected = false
    @State private var isChecking = false
    let timer = Timer.publish(every: 3, on: .main, in: .common).autoconnect()

    var body: some View {
        HStack(alignment: .center) {
            SettingsRowLabel(
                label: "Google Calendar",
                description: isConnected
                    ? "Connected — events sync every 30s"
                    : "Link your calendar to see upcoming events"
            )
            Spacer()

            if isConnected {
                HStack(spacing: 6) {
                    Circle()
                        .fill(ADHDColors.Accent.success)
                        .frame(width: 8, height: 8)
                    Text("Connected")
                        .font(Font.custom("Lexend-Medium", size: 13))
                        .foregroundColor(ADHDColors.Accent.success)
                }
                .padding(.vertical, 6)
                .padding(.horizontal, 14)
                .background(ADHDColors.Accent.success.opacity(0.1))
                .cornerRadius(10)
            } else {
                Button {
                    guard let url = URL(string: "http://\(backendURL)/api/auth/google") else { return }
                    NSWorkspace.shared.open(url)
                } label: {
                    Text("Connect")
                        .font(Font.custom("Lexend-Medium", size: 13))
                        .foregroundColor(ADHDColors.Accent.focusLight)
                        .padding(.vertical, 6)
                        .padding(.horizontal, 14)
                        .background(ADHDColors.Accent.focusLight.opacity(0.1))
                        .cornerRadius(10)
                }
                .buttonStyle(.plain)
            }
        }
        .task {
            await checkStatus()
        }
        .onReceive(timer) { _ in
            Task { await checkStatus() }
        }
    }

    private func checkStatus() async {
        guard !isChecking else { return }
        isChecking = true
        defer { isChecking = false }

        guard let url = URL(string: "http://\(backendURL)/api/auth/google/status") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            struct Status: Decodable { let connected: Bool }
            if let status = try? JSONDecoder().decode(Status.self, from: data) {
                isConnected = status.connected
            }
        } catch {
            // Backend not reachable
        }
    }
}

// MARK: - Placeholder for unimplemented tabs

private struct PlaceholderSettingsPage: View {
    let title: String

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(title)
                .font(Font.custom("Lexend-SemiBold", size: 18))
                .foregroundColor(ADHDColors.Text.primary)
        }
        .padding(.vertical, 24)
        .padding(.horizontal, 28)
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }
}

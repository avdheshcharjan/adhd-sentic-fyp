import SwiftUI

/// Step-by-step permission setup wizard.
/// Guides the user through granting Accessibility and Automation permissions.
///
/// Supplement Section 2: Screen Recording removed. Only Accessibility + Automation needed.
/// Anti-pattern #6: NEVER use Screen Recording for core monitoring.
struct OnboardingView: View {

    @State private var hasAccessibility = Permissions.hasAccessibility
    @State private var refreshTimer: Timer?

    var body: some View {
        VStack(spacing: 24) {
            // Header
            VStack(spacing: 8) {
                Image(systemName: "brain.head.profile")
                    .font(.system(size: 48))
                    .foregroundStyle(.orange)
                Text("ADHD Second Brain")
                    .font(.title.bold())
                Text("One permission needed to enable focus monitoring")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }

            Divider()

            // Permission List
            VStack(spacing: 16) {
                PermissionRow(
                    title: "Accessibility",
                    description: "Read window titles and observe app switches (one-time grant)",
                    systemImage: "hand.raised",
                    isGranted: hasAccessibility
                ) {
                    Permissions.requestAccessibility()
                }

                PermissionRow(
                    title: "Automation",
                    description: "Extract browser URLs (granted automatically per browser)",
                    systemImage: "applescript",
                    isGranted: true // Auto-granted on first AppleScript run
                ) { }
            }

            Divider()

            if hasAccessibility {
                Label("All permissions granted — monitoring is active!", systemImage: "checkmark.circle.fill")
                    .foregroundColor(.green)
                    .font(.callout.bold())
            } else {
                Text("After granting Accessibility, the app will start monitoring automatically.")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(32)
        .frame(width: 480)
        .onAppear {
            refreshTimer = Timer.scheduledTimer(withTimeInterval: 2, repeats: true) { _ in
                hasAccessibility = Permissions.hasAccessibility
            }
        }
        .onDisappear {
            refreshTimer?.invalidate()
        }
    }
}

/// Single permission row with status indicator and action button.
struct PermissionRow: View {
    let title: String
    let description: String
    let systemImage: String
    let isGranted: Bool
    let onRequest: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: systemImage)
                .font(.title2)
                .foregroundStyle(isGranted ? .green : .orange)
                .frame(width: 32)

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.body.bold())
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            if isGranted {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(.green)
            } else {
                Button("Grant") {
                    onRequest()
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.small)
            }
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 10)
                .fill(isGranted ? Color.green.opacity(0.05) : Color.orange.opacity(0.05))
        )
    }
}

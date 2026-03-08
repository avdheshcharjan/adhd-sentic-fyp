import SwiftUI

/// Step-by-step permission setup wizard.
/// Guides the user through granting Screen Recording, Accessibility, and Automation permissions.
struct OnboardingView: View {

    @State private var hasScreenRecording = Permissions.hasScreenRecording
    @State private var hasAccessibility = Permissions.hasAccessibility
    @State private var refreshTimer: Timer?

    var allGranted: Bool {
        hasScreenRecording && hasAccessibility
    }

    var body: some View {
        VStack(spacing: 24) {
            // Header
            VStack(spacing: 8) {
                Image(systemName: "brain.head.profile")
                    .font(.system(size: 48))
                    .foregroundStyle(.purple)
                Text("ADHD Second Brain")
                    .font(.title.bold())
                Text("Grant these permissions to enable focus monitoring")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }

            Divider()

            // Permission List
            VStack(spacing: 16) {
                PermissionRow(
                    title: "Screen Recording",
                    description: "Read window titles to classify your activity",
                    systemImage: "rectangle.on.rectangle",
                    isGranted: hasScreenRecording
                ) {
                    Permissions.requestScreenRecording()
                }

                PermissionRow(
                    title: "Accessibility",
                    description: "Observe app switches and window focus",
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

            if allGranted {
                Label("All permissions granted — monitoring is active!", systemImage: "checkmark.circle.fill")
                    .foregroundColor(.green)
                    .font(.callout.bold())
            } else {
                Text("After granting permissions, you may need to restart the app.")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(32)
        .frame(width: 480)
        .onAppear {
            // Poll permission status every 2 seconds
            refreshTimer = Timer.scheduledTimer(withTimeInterval: 2, repeats: true) { _ in
                hasScreenRecording = Permissions.hasScreenRecording
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

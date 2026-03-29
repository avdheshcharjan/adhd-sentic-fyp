import SwiftUI

@main
struct ADHDSecondBrainApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        MenuBarExtra {
            MenuBarView(coordinator: appDelegate.coordinator)
        } label: {
            Image(systemName: "brain.head.profile")
        }
        .menuBarExtraStyle(.window)

        Window("Dashboard", id: "dashboard") {
            DashboardView(coordinator: appDelegate.coordinator)
        }
        .windowStyle(.hiddenTitleBar)
        .defaultSize(width: 960, height: 800)

        Window("History", id: "history") {
            HistoryView()
        }
        .windowStyle(.hiddenTitleBar)
        .defaultSize(width: 960, height: 700)

        Settings {
            SettingsView()
        }
    }
}


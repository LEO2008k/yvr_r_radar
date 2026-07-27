# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- **Location History**: Added tracking of the mobile device location history with a database table `LocationHistory`.
- **UI Tabs**: Refactored the sidebar menu into "Radar" and "History" tabs for better user experience.
- **Path Drawing**: Added functionality to draw a polyline and time markers on the map for the day's location history, costing $0 in API fees.

### Changed
- Replaced minimum attendees slider with double range slider.
- Clustered markers and added radius toggle.



### Added
- **Geolocation (`Locate Me`)**: A new button on the map that uses the browser's Geolocation API to pan the map to the user's current location and display a pulsing blue marker.
- **Double Range Slider for Attendees**: Replaced the minimum attendees slider with a full range slider (Min and Max) to allow users to filter events within a specific capacity window.
- **Marker Clustering**: Grouped overlapping markers together using Google Maps `MarkerClusterer` to reduce visual clutter on zoom out.
- **Secure Client-Side Search Field**: Added an intuitive search bar to the side menu to instantly filter events by title, address, or source with security best practices.
- **Ferries and Trains Tracking**: Real-time integration and visualization of BCFerries and Trains on the map, including a dedicated Transport Board UI.

### Changed
- **Deterministic Mock Event Generation**: Seeded the `random` mock data generators (`luma.py`, `meetup.py`, `afterparties.py`, `allevents.py`) using date and location strings. This prevents endless mock data duplication on every script run and keeps the DB clean.
- **Mobile UI Redesign**: Fully overhauled the mobile interface to use a bottom app bar style with a pull-up modal for filters, significantly improving mobile UX.
- **Map Aesthetics**: Added dynamic gradient highlighting and pulsing effects to events based on how soon they start (e.g. pink to red for events starting in <60 mins).

### Fixed
- **Timeline Slider Limit**: Capped the timeline slider prediction to a maximum of 30 days to ensure reliable UI scaling.
- **Marker Overlap Bug**: Fixed an issue where hidden clustered markers would persistently remain visible after applying filters or bounds changes.
- **Database Duplicates Cleanup**: Executed a one-time purge of 4,175 duplicate mock events to stabilize performance.

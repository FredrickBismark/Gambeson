// V-Groove Rail Track for Ball Bearing Helmet Interface
// Parametric semi-circular bearing track mounted on collar substrate
//
// Requires BOSL2: https://github.com/BelfrySCAD/BOSL2
// Render: openscad -o output/rail_track.stl models/rail_track.scad -D 'size_index=2'

include <BOSL2/std.scad>
include <BOSL2/paths.scad>

// Size grading table: [name, arc_radius, arc_length]
sizes = [
    ["S",  110, 190],
    ["M",  120, 200],
    ["L",  125, 210],
    ["XL", 130, 220],
    ["XXL", 135, 230]
];

size_index = 1;  // Default: M

// Resolved parameters
arc_radius = sizes[size_index][1];
arc_length = sizes[size_index][2];
arc_angle  = arc_length / arc_radius * 180 / PI;

// Track cross-section parameters
track_width  = 55;   // mm, total track width
track_depth  = 18;   // mm, track depth
wall_thick   = 4;    // mm, side wall thickness
groove_angle = 90;   // degrees, V-groove angle
groove_depth = 6;    // mm, V-groove depth
lip_height   = 3;    // mm, retention lip to prevent disengagement

// V-groove profile (2D cross-section)
module v_groove_profile() {
    half_groove = groove_depth * tan(groove_angle / 2);
    half_width  = track_width / 2;

    // Main channel profile with V-groove at bottom center
    polygon([
        // Left wall outer
        [-half_width, track_depth],
        [-half_width, 0],
        // Left floor to groove
        [-half_groove, 0],
        // V-groove
        [0, -groove_depth],
        // Right floor from groove
        [half_groove, 0],
        // Right wall outer
        [half_width, 0],
        [half_width, track_depth],
        // Retention lips (inward-facing)
        [half_width - wall_thick, track_depth],
        [half_width - wall_thick, track_depth - lip_height],
        // Inner channel right
        [half_width - wall_thick, wall_thick],
        // Inner floor right
        [half_groove + wall_thick, wall_thick],
        // Inner V-groove
        [0, -groove_depth + wall_thick],
        // Inner floor left
        [-half_groove - wall_thick, wall_thick],
        // Inner channel left
        [-half_width + wall_thick, wall_thick],
        [-half_width + wall_thick, track_depth - lip_height],
        [-half_width + wall_thick, track_depth],
    ]);
}

// Sweep the V-groove profile along a circular arc
module rail_track() {
    // Generate arc path
    arc_steps = 60;
    half_angle = arc_angle / 2;

    rotate([90, 0, 0])
    rotate_extrude(angle = arc_angle, $fn = arc_steps)
    translate([arc_radius, 0, 0])
    rotate([0, 0, 90])
    v_groove_profile();
}

// Mounting holes for attaching track to HDPE collar substrate
module mounting_holes() {
    hole_d    = 5.5;  // M5 clearance
    num_holes = 6;

    for (i = [0:num_holes - 1]) {
        angle = i * arc_angle / (num_holes - 1);
        rotate([0, 0, angle])
        translate([arc_radius, 0, -groove_depth - 2])
        cylinder(d = hole_d, h = track_depth + groove_depth + 4, $fn = 20);
    }
}

// Final assembly
module rail_track_assembly() {
    difference() {
        // Center the arc
        rotate([0, 0, -arc_angle / 2])
        rail_track();

        rotate([0, 0, -arc_angle / 2])
        mounting_holes();
    }
}

rail_track_assembly();

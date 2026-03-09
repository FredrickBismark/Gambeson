// Helmet Attachment Rail Segment
// Mates with the V-groove collar track for frictionless rotation
//
// This rail attaches to the helmet and rides in the collar track.
// V-groove wheels are mounted on this rail.
//
// Requires BOSL2: https://github.com/BelfrySCAD/BOSL2
// Render: openscad -o output/helmet_rail.stl models/helmet_rail.scad

include <BOSL2/std.scad>

// Size grading (must match rail_track.scad)
sizes = [
    ["S",  110, 190],
    ["M",  120, 200],
    ["L",  125, 210],
    ["XL", 130, 220],
    ["XXL", 135, 230]
];

size_index = 1;  // Default: M

arc_radius = sizes[size_index][1];
arc_length = sizes[size_index][2];
arc_angle  = arc_length / arc_radius * 180 / PI;

// Rail parameters
rail_width     = 20;    // mm, narrower than track to fit inside
rail_thickness = 5;     // mm
rail_arc_angle = arc_angle * 0.7;  // Shorter than track to allow rotation range

// Wheel axle mounting parameters
wheel_diameter = 9;     // mm, V-groove bearing wheel
axle_diameter  = 4;     // mm, axle bolt
num_wheels     = 4;     // wheels along the rail

// Helmet mounting plate
plate_width    = 60;    // mm
plate_height   = 40;    // mm
plate_thick    = 4;     // mm

// Rail cross-section profile
module rail_profile() {
    half_w = rail_width / 2;
    // Simple rectangular rail with slight taper for track engagement
    polygon([
        [-half_w, 0],
        [-half_w + 2, -rail_thickness],
        [half_w - 2, -rail_thickness],
        [half_w, 0],
    ]);
}

// Curved rail body
module rail_body() {
    rotate([90, 0, 0])
    rotate_extrude(angle = rail_arc_angle, $fn = 48)
    translate([arc_radius, 0, 0])
    rotate([0, 0, 90])
    rail_profile();
}

// Wheel axle holes along the rail
module wheel_axles() {
    for (i = [0:num_wheels - 1]) {
        angle = i * rail_arc_angle / (num_wheels - 1);
        rotate([0, 0, angle])
        translate([arc_radius, 0, -rail_thickness / 2])
        rotate([0, 90, 0])
        cylinder(d = axle_diameter, h = rail_width + 10, center = true, $fn = 16);
    }
}

// Helmet mounting plate at the top center of the rail
module helmet_mount_plate() {
    mid_angle = rail_arc_angle / 2;
    rotate([0, 0, mid_angle])
    translate([arc_radius, 0, plate_thick / 2]) {
        difference() {
            cube([plate_width, plate_height, plate_thick], center = true);
            // Mounting bolt holes (4x M5)
            for (x = [-plate_width / 2 + 10, plate_width / 2 - 10])
            for (y = [-plate_height / 2 + 10, plate_height / 2 - 10])
                translate([x, y, 0])
                cylinder(d = 5.5, h = plate_thick + 2, center = true, $fn = 16);
        }
    }
}

// Quick-release detent hole
module detent_hole() {
    // Spring-loaded ball detent at one end of the rail
    rotate([0, 0, 2])
    translate([arc_radius, 0, 0])
    cylinder(d = 8, h = rail_thickness + 2, center = true, $fn = 16);
}

// Assembly
module helmet_rail_assembly() {
    difference() {
        union() {
            rotate([0, 0, -rail_arc_angle / 2])
            rail_body();
            helmet_mount_plate();
        }
        rotate([0, 0, -rail_arc_angle / 2])
        wheel_axles();
        detent_hole();
    }
}

helmet_rail_assembly();

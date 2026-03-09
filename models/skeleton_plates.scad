// HDPE Skeleton Plates — All structural components
// Collar substrate, shoulder yokes, spine segments, lumbar bridge
//
// Render individual parts:
//   openscad -o output/collar.stl models/skeleton_plates.scad -D 'part="collar"'
//   openscad -o output/yoke_left.stl models/skeleton_plates.scad -D 'part="yoke"'
//   openscad -o output/spine_segment.stl models/skeleton_plates.scad -D 'part="spine"'
//   openscad -o output/lumbar.stl models/skeleton_plates.scad -D 'part="lumbar"'
//   openscad -o output/skeleton_assembly.stl models/skeleton_plates.scad -D 'part="assembly"'

// Size grading
sizes = [
    // [name, neck_radius, chest_width, torso_height]
    ["S",  110, 420, 419],
    ["M",  120, 440, 445],
    ["L",  125, 460, 470],
    ["XL", 130, 480, 496],
    ["XXL", 135, 500, 521]
];

size_index = 1;  // Default: M
part = "assembly";  // collar, yoke, spine, lumbar, assembly

// Resolved dimensions
neck_r   = sizes[size_index][1];
chest_w  = sizes[size_index][2];
torso_h  = sizes[size_index][3];

// Common parameters
hdpe_t = 6;      // mm, HDPE sheet thickness
fillet = 3;      // mm, edge rounding (approximate with minkowski)
bolt_d = 5.5;    // mm, M5 clearance hole

// ============================================================
// Collar Substrate
// Curved plate following the back of the neck
// ============================================================
collar_arc_length = 200;  // mm
collar_width      = 55;   // mm
collar_arc_angle  = collar_arc_length / neck_r * 180 / PI;

module collar() {
    difference() {
        // Arc-shaped plate
        rotate([90, 0, 0])
        rotate_extrude(angle = collar_arc_angle, $fn = 48)
        translate([neck_r, 0, 0])
        square([hdpe_t, collar_width]);

        // Bearing rail mounting holes (6x M5)
        for (i = [0:5]) {
            angle = i * collar_arc_angle / 5;
            rotate([0, 0, angle])
            translate([neck_r + hdpe_t / 2, 0, collar_width / 2])
            rotate([0, 90, 0])
            cylinder(d = bolt_d, h = hdpe_t + 4, center = true, $fn = 16);
        }

        // Shoulder yoke attachment holes (2x each side)
        for (angle = [5, collar_arc_angle - 5])
        for (z = [15, collar_width - 15]) {
            rotate([0, 0, angle])
            translate([neck_r + hdpe_t / 2, 0, z])
            rotate([0, 90, 0])
            cylinder(d = bolt_d, h = hdpe_t + 4, center = true, $fn = 16);
        }
    }
}

// ============================================================
// Shoulder Yoke
// Curved plate following shoulder contour, tapers from 80mm to 50mm
// ============================================================
yoke_length    = 200;  // mm
yoke_w_top     = 80;   // mm at shoulder
yoke_w_bottom  = 50;   // mm at chest

module shoulder_yoke() {
    // Trapezoidal plate
    yoke_t = 5;  // mm, slightly thinner than main skeleton

    difference() {
        linear_extrude(height = yoke_t)
        polygon([
            [0, 0],
            [yoke_length, 0],
            [yoke_length, yoke_w_bottom],
            [0, yoke_w_top],
        ]);

        // Collar pivot hole at top
        translate([15, yoke_w_top / 2, -1])
        cylinder(d = 8, h = yoke_t + 2, $fn = 20);

        // MOLLE slot pattern (3 rows of slots)
        for (row = [0:2])
        for (col = [0:3]) {
            x = 40 + col * 35;
            y = 12 + row * 25;
            if (y + 12 < yoke_w_bottom) {  // Only if within taper
                translate([x, y, -1])
                hull() {
                    cylinder(d = 4, h = yoke_t + 2, $fn = 12);
                    translate([20, 0, 0])
                    cylinder(d = 4, h = yoke_t + 2, $fn = 12);
                }
            }
        }

        // Front plate carrier attachment holes
        for (y = [15, yoke_w_bottom - 15])
        translate([yoke_length - 15, y, -1])
        cylinder(d = bolt_d, h = yoke_t + 2, $fn = 16);
    }
}

// ============================================================
// Spine Segment
// One of 4 overlapping segments forming the articulated spine plate
// ============================================================
spine_w = 150;   // mm
spine_h = 100;   // mm
spine_overlap = 25;  // mm between segments

module spine_segment() {
    difference() {
        // Slight curvature via shallow cylinder section
        intersection() {
            cube([spine_w, spine_h, hdpe_t]);
            translate([spine_w / 2, -300, 0])
            cylinder(r = 350, h = hdpe_t, $fn = 60);
        }

        // Webbing channel slots (for inter-segment connection)
        // 2" (50mm) webbing slots at each side
        for (x = [20, spine_w - 70])
        for (y = [10, spine_h - 20]) {
            translate([x, y, -1])
            cube([50, 6, hdpe_t + 2]);
        }

        // Center bolt holes for optional rigid connection
        for (x = [spine_w / 2 - 20, spine_w / 2 + 20])
        for (y = [15, spine_h - 15]) {
            translate([x, y, -1])
            cylinder(d = bolt_d, h = hdpe_t + 2, $fn = 16);
        }

        // Corner radii (approximate rounded corners)
        r = 8;
        for (corner = [[0, 0], [spine_w, 0], [spine_w, spine_h], [0, spine_h]]) {
            translate([corner[0], corner[1], -1])
            difference() {
                cube([r, r, hdpe_t + 2]);
                translate([corner[0] == 0 ? r : 0,
                          corner[1] == 0 ? r : 0, 0])
                cylinder(r = r, h = hdpe_t + 2, $fn = 20);
            }
        }
    }
}

// ============================================================
// Lumbar Bridge
// Wider plate connecting spine to hip belt with sliding attachment
// ============================================================
lumbar_w = 200;  // mm
lumbar_h = 150;  // mm

module lumbar_bridge() {
    difference() {
        // Main plate with slight curve
        intersection() {
            cube([lumbar_w, lumbar_h, hdpe_t]);
            translate([lumbar_w / 2, -250, 0])
            cylinder(r = 300, h = hdpe_t, $fn = 60);
        }

        // Sliding hip belt track (elongated slot for belt attachment)
        // Allows 20mm of sliding motion for gait accommodation
        for (x = [30, lumbar_w - 30]) {
            translate([x - 3, lumbar_h - 30, -1])
            hull() {
                cylinder(d = 8, h = hdpe_t + 2, $fn = 16);
                translate([0, -20, 0])
                cylinder(d = 8, h = hdpe_t + 2, $fn = 16);
            }
        }

        // Spine plate attachment holes (top edge)
        for (x = [lumbar_w / 2 - 30, lumbar_w / 2 + 30])
        for (y = [15, 35]) {
            translate([x, y, -1])
            cylinder(d = bolt_d, h = hdpe_t + 2, $fn = 16);
        }

        // D3O insert pocket outline (kidney protection area)
        translate([lumbar_w / 2 - 50, 40, hdpe_t - 2])
        cube([100, 80, 3]);

        // Webbing slots for hip belt connection
        for (x = [15, lumbar_w - 65])
        translate([x, lumbar_h - 15, -1])
        cube([50, 6, hdpe_t + 2]);
    }
}

// ============================================================
// Assembly view
// ============================================================
module skeleton_assembly() {
    // Collar (centered at back of neck)
    color("SteelBlue")
    translate([0, 0, torso_h - 20])
    rotate([0, 0, -collar_arc_angle / 2])
    collar();

    // Left shoulder yoke
    color("CadetBlue")
    translate([-chest_w / 2 + 20, -50, torso_h - 60])
    rotate([80, 0, -10])
    shoulder_yoke();

    // Right shoulder yoke (mirrored)
    color("CadetBlue")
    translate([chest_w / 2 - 20, -50, torso_h - 60])
    rotate([80, 0, 10])
    mirror([1, 0, 0])
    shoulder_yoke();

    // Spine segments (stacked with overlap)
    color("SlateGray")
    for (i = [0:3]) {
        translate([
            -spine_w / 2,
            chest_w * 0.35 - hdpe_t,
            torso_h - 80 - i * (spine_h - spine_overlap)
        ])
        rotate([90, 0, 0])
        spine_segment();
    }

    // Lumbar bridge
    color("DarkSlateGray")
    translate([-lumbar_w / 2, chest_w * 0.35 - hdpe_t, 30])
    rotate([90, 0, 0])
    lumbar_bridge();
}

// Part selector
if (part == "collar") {
    collar();
} else if (part == "yoke") {
    shoulder_yoke();
} else if (part == "spine") {
    spine_segment();
} else if (part == "lumbar") {
    lumbar_bridge();
} else {
    skeleton_assembly();
}

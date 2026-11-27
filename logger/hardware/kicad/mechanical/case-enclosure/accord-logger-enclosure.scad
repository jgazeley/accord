// SPDX-License-Identifier: CERN-OHL-P-2.0
// Copyright 2026 Jayson Gazeley — https://github.com/jgazeley/accord
// mm. Requires ../case-bottom/accord-logger-case-bottom.stl as the base blank.
part = "top"; // top (roof down), bottom, assembled, exploded
engagement = 0.4; // 0.1..0.6; regenerate BOTH parts after fitting changes
lip_clearance = 0.3; // radial, 0.2..0.5
pcb_headroom = 25; // PCB top to roof underside; mating geometry stays fixed
sd_center_x = 41.2675;
sd_width = 29.8; // gap matches lower SD window
pcb_top_z = 8.775;
roof = 2;
top_z = pcb_top_z+pcb_headroom+roof;
assert(pcb_headroom >= 18.225);
$fn = 128;
assert(engagement >= 0.1 && engagement <= 0.6);
assert(lip_clearance >= 0.2 && lip_clearance <= 0.5);
module rounded(gap, z0, z1, upper_gap=undef) {
    hull() for (x=[2,118]) for(y=[2,81]) translate([x,y,z0])
        cylinder(h=z1-z0, r1=2+gap, r2=2+(is_undef(upper_gap)?gap:upper_gap));
}
module receivers() {
    for(x=[18,102]) for(y=[-3.1,83.9])
        translate([x-4.5,y,12.6]) cube([9,2.2,2.2]);
}
module bottom() {
    difference() {
        import("../case-bottom/accord-logger-case-bottom.stl", convexity=10);
        receivers();
    }
}
module clips() {
    for(x=[18,102]) for(side=[[-3,-1],[86,1]])
        multmatrix([[0,0,1,x-4],[side[1],0,0,side[0]],[0,1,0,0],[0,0,0,1]]) {
            linear_extrude(height=8) polygon([[0.3, 12.8], [1.5, 12.8], [1.5, 26.9], [-0.3, 28.7], [-0.3, 25], [-0.24118971580226353, 24.997110836003316], [-0.182945806790323, 24.988471168241936], [-0.1258291936473226, 24.974164201439322], [-0.07038994058094611, 24.95432771950677], [-0.017161957904401337, 24.92915275860901], [0.03334213981176137, 24.898881767381525], [0.08063597049818727, 24.86380627201764], [0.12426406871192852, 24.824264068711926], [0.1638062720176422, 24.780635970498185], [0.19888176738152713, 24.73334213981176], [0.2291527586090129, 24.682838042095597], [0.2543277195067721, 24.629610059419054], [0.27416420143932535, 24.574170806352676], [0.28847116824193825, 24.517054193209674], [0.29711083600331817, 24.458810284197735], [0.3, 24.4]]);
            linear_extrude(height=8) polygon([[0.35,12.8],[0.35,14.6],
                [-engagement,14.6],[-engagement,14],[0.3,12.8]]);
        }
}
module lid() {
    union() {
        difference() {
            union() {
                difference() { rounded(3,16,top_z); rounded(1,15.9,top_z-roof); }
                difference() {
                    rounded(1-lip_clearance,13,16.1);
                    rounded(-lip_clearance,12.9,16.2);
                }
                difference() {
                    rounded(1.2,16,17.5); rounded(-lip_clearance,16,17.5,1);
                }
            }
            // Cut wall AND alignment skirt to complete the lower JAE notch.
            translate([118,26,8.275]) cube([5.2,28,16.5]);
            // Remove the thin inner skirt below the Z=16 seam above SD access.
            translate([sd_center_x-sd_width/2,-5,0]) cube([sd_width,6,16]);
        }
        clips();
    }
}
if(part=="bottom") bottom();
else if(part=="top") translate([0,83,top_z]) rotate([180,0,0]) lid();
else if(part=="assembled" || part=="exploded") {
    color([0.39,0.61,0.77]) bottom();
    color([0.88,0.64,0.35]) translate([0,0,part=="exploded"?24:0]) lid();
}
else assert(false,"Unknown part selector");

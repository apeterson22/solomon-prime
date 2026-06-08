$fn=50;
module test_part() {
    difference() {
        cylinder(h=10, r=10, center=true);
        cylinder(h=12, r=5, center=true);
    }
}
test_part();

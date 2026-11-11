#[test]
fn assert_in_loop() {
    for value in [1, 2] {
        assert!(value > 0);
    }
}

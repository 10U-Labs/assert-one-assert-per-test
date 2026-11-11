#[test]
#[should_panic(expected = "boom")]
fn should_panic_with_expected() {
    panic!("boom");
}

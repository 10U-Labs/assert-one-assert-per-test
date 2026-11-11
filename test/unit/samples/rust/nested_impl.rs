#[test]
fn nested_impl() {
    struct Checker;
    impl Checker {
        fn check(&self) {
            assert!(false);
        }
    }
    assert!(true);
}

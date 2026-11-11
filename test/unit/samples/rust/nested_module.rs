#[test]
fn nested_module() {
    mod inner {
        fn check() {
            assert!(false);
        }
    }
    assert!(true);
}

#[test]
fn nested_trait() {
    trait Check {
        fn check(&self) {
            assert!(false);
        }
    }
    assert!(true);
}

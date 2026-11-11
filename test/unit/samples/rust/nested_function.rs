#[test]
fn nested_function() {
    fn helper() {
        assert!(false);
    }
    assert!(true);
}

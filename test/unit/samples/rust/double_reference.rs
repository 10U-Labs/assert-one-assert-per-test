#[test]
fn double_reference() {
    let value = 1;
    assert!(&&value == &&1);
}

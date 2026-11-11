#[test]
fn conjunction_under_disjunction() {
    assert!(false || true && true);
}

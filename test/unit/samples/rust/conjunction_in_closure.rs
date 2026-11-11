#[test]
fn conjunction_in_closure() {
    assert!([1, 2].iter().all(|value| *value > 0 && *value < 3));
}

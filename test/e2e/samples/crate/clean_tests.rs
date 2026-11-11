use example::add;

#[test]
fn adds_from_outside() {
    assert_eq!(add(2, 2), 4);
}

#[test]
fn assert_in_closure() {
    [1, 2].iter().for_each(|value| assert!(*value > 0));
}

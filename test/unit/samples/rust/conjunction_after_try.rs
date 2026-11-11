#[test]
fn conjunction_after_try() -> Result<(), String> {
    assert!(ready()? && true);
    Ok(())
}

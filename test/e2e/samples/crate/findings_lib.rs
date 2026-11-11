pub fn add(left: i32, right: i32) -> i32 {
    left + right
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn adds() {
        let _sum = add(1, 2);
    }

    #[test]
    fn adds_twice() {
        assert_eq!(add(1, 2), 3);
        assert_eq!(add(2, 2), 4);
    }

    #[test]
    fn adds_both() -> Result<(), String> {
        assert!(checked(1)? && add(1, 1) == 2);
        Ok(())
    }

    #[test]
    #[should_panic]
    fn overflows() {
        assert!(add(i32::MAX, 1) > 0);
    }
}

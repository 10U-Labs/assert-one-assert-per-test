pub fn add(left: i32, right: i32) -> i32 {
    left + right
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn adds() {
        assert_eq!(add(1, 2), 3);
    }

    #[test]
    // the sum of nothing is nothing
    fn adds_zero() {
        assert!(add(0, 0) == 0 || add(0, 1) == 0);
    }

    #[test]
    #[should_panic(expected = "overflow")]
    fn overflows() {
        add(i32::MAX, 1);
    }

    #[test]
    fn adds_each() {
        fn check(value: i32) {
            assert!(value > 0);
        }
        struct Pair;
        impl Pair {
            fn check(&self) {
                assert!(true);
            }
        }
        [1, 2].iter().for_each(|value| assert!(add(*value, 0) > 0, "{}", true && true));
    }

    #[tokio::test]
    async fn adds_references() {
        assert!(&&add(1, 1) == &&2);
    }
}

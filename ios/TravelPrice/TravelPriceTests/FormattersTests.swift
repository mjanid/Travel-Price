import XCTest
@testable import TravelPrice

final class FormattersTests: XCTestCase {

    func testPriceFormatting() {
        XCTAssertEqual(Formatters.price(cents: 12345, currency: "USD"), "$123.45")
        XCTAssertEqual(Formatters.price(cents: 0, currency: "USD"), "$0.00")
        XCTAssertEqual(Formatters.price(cents: 100, currency: "USD"), "$1.00")
    }

    func testDollarsToCents() {
        XCTAssertEqual(Formatters.dollarsToCents("123.45"), 12345)
        XCTAssertEqual(Formatters.dollarsToCents("$1,234.56"), 123456)
        XCTAssertEqual(Formatters.dollarsToCents("0"), 0)
        XCTAssertNil(Formatters.dollarsToCents("abc"))
        XCTAssertNil(Formatters.dollarsToCents(""))
    }

    func testIATACode() {
        XCTAssertEqual(Formatters.iataCode("jfk"), "JFK")
        XCTAssertEqual(Formatters.iataCode("  lax  "), "LAX")
        XCTAssertEqual(Formatters.iataCode("abcde"), "ABC")
    }

    func testApiDate() {
        let date = Calendar.current.date(from: DateComponents(year: 2026, month: 6, day: 15))!
        XCTAssertEqual(Formatters.apiDate(date), "2026-06-15")
    }

    func testDisplayDate() {
        let result = Formatters.displayDate("2026-06-15")
        XCTAssertTrue(result.contains("2026"))
        XCTAssertTrue(result.contains("Jun") || result.contains("15"))
    }
}

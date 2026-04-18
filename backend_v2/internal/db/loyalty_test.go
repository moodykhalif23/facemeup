package db

import "testing"

func TestTierThresholds(t *testing.T) {
	cases := []struct {
		bal       int
		tier      string
		toNext    int
		nextTier  string
	}{
		{0,    "Bronze",   500,  "Silver"},
		{499,  "Bronze",   1,    "Silver"},
		{500,  "Silver",   500,  "Gold"},
		{999,  "Silver",   1,    "Gold"},
		{1000, "Gold",     1000, "Platinum"},
		{1500, "Gold",     500,  "Platinum"},
		{2000, "Platinum", 0,    ""},
		{5000, "Platinum", 0,    ""},
	}
	for _, tc := range cases {
		name, toNext, next := Tier(tc.bal)
		if name != tc.tier || toNext != tc.toNext || next != tc.nextTier {
			t.Errorf("Tier(%d)=(%q,%d,%q) want (%q,%d,%q)",
				tc.bal, name, toNext, next, tc.tier, tc.toNext, tc.nextTier)
		}
	}
}

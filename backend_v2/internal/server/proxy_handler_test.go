package server

import (
	"net"
	"testing"
)

func TestValidateProxyURLAccepts(t *testing.T) {
	tests := []string{
		"https://drrashel.co.ke/image.jpg",
		"http://example.com/x.png",
	}
	for _, u := range tests {
		if _, err := validateProxyURL(u); err != nil {
			t.Errorf("%q should be accepted: %v", u, err)
		}
	}
}

func TestValidateProxyURLRejects(t *testing.T) {
	bad := []string{
		"",
		"ftp://example.com",
		"file:///etc/passwd",
		"gopher://example.com",
		"javascript:alert(1)",
		"not-a-url",
		"https://",
	}
	for _, u := range bad {
		if _, err := validateProxyURL(u); err == nil {
			t.Errorf("%q should be rejected", u)
		}
	}
}

func TestIsPrivateIPDetectsLoopbackAndRFC1918(t *testing.T) {
	privates := []string{"127.0.0.1", "10.0.0.5", "192.168.1.1", "172.16.0.3", "100.64.1.1", "::1", "fe80::1"}
	for _, p := range privates {
		if !isPrivateIP(net.ParseIP(p)) {
			t.Errorf("%q should be private", p)
		}
	}
	publics := []string{"8.8.8.8", "1.1.1.1", "203.0.113.5"}
	for _, p := range publics {
		if isPrivateIP(net.ParseIP(p)) {
			t.Errorf("%q should NOT be private", p)
		}
	}
}

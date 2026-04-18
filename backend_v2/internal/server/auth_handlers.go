package server

import (
	"encoding/json"
	"errors"
	"net/http"
	"strings"
	"time"

	"github.com/google/uuid"

	"skincare/backend-v2/internal/auth"
	"skincare/backend-v2/internal/db"
)

type signupRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
	FullName string `json:"full_name"`
}

type loginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type authResponse struct {
	AccessToken string `json:"access_token"`
	TokenType   string `json:"token_type"`
	ExpiresAt   string `json:"expires_at"`
	UserID      string `json:"user_id"`
	Email       string `json:"email"`
	Role        string `json:"role"`
	FullName    string `json:"full_name,omitempty"`
}

type meResponse struct {
	ID       string `json:"id"`
	Email    string `json:"email"`
	Role     string `json:"role"`
	FullName string `json:"full_name,omitempty"`
}

func (s *Server) handleSignup(w http.ResponseWriter, r *http.Request) {
	var req signupRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "invalid JSON body")
		return
	}
	req.Email = strings.TrimSpace(strings.ToLower(req.Email))
	if req.Email == "" || !strings.Contains(req.Email, "@") {
		writeError(w, http.StatusBadRequest, "invalid_email", "email is required")
		return
	}
	if len(req.Password) < 6 {
		writeError(w, http.StatusBadRequest, "weak_password", "password must be at least 6 characters")
		return
	}

	hash, err := auth.HashPassword(req.Password)
	if err != nil {
		s.log.Error("hash password", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not process signup")
		return
	}

	full := strings.TrimSpace(req.FullName)
	var fullPtr *string
	if full != "" {
		fullPtr = &full
	}
	user := &db.User{
		ID:           uuid.NewString(),
		Email:        req.Email,
		PasswordHash: hash,
		FullName:     fullPtr,
		Role:         db.RoleCustomer,
		CreatedAt:    time.Now().UTC(),
	}

	if err := s.deps.Users.Insert(r.Context(), user); err != nil {
		if errors.Is(err, db.ErrEmailTaken) {
			writeError(w, http.StatusConflict, "email_taken", "email already registered")
			return
		}
		s.log.Error("insert user", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not create user")
		return
	}

	s.issueAndRespond(w, user)
}

func (s *Server) handleLogin(w http.ResponseWriter, r *http.Request) {
	var req loginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "invalid JSON body")
		return
	}
	req.Email = strings.TrimSpace(strings.ToLower(req.Email))
	if req.Email == "" || req.Password == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "email and password required")
		return
	}

	user, err := s.deps.Users.GetByEmail(r.Context(), req.Email)
	if err != nil {
		if errors.Is(err, db.ErrUserNotFound) {
			writeError(w, http.StatusUnauthorized, "invalid_credentials", "invalid email or password")
			return
		}
		s.log.Error("get user by email", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "login failed")
		return
	}

	if err := auth.VerifyPassword(user.PasswordHash, req.Password); err != nil {
		if errors.Is(err, auth.ErrWrongPassword) {
			writeError(w, http.StatusUnauthorized, "invalid_credentials", "invalid email or password")
			return
		}
		s.log.Error("verify password", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "login failed")
		return
	}

	s.issueAndRespond(w, user)
}

func (s *Server) handleMe(w http.ResponseWriter, r *http.Request) {
	p := auth.PrincipalFrom(r.Context())
	if p == nil {
		writeError(w, http.StatusUnauthorized, "unauthenticated", "not logged in")
		return
	}

	user, err := s.deps.Users.GetByID(r.Context(), p.UserID)
	if err != nil {
		if errors.Is(err, db.ErrUserNotFound) {
			writeError(w, http.StatusNotFound, "not_found", "user no longer exists")
			return
		}
		s.log.Error("get user by id", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "lookup failed")
		return
	}

	resp := meResponse{ID: user.ID, Email: user.Email, Role: user.Role}
	if user.FullName != nil {
		resp.FullName = *user.FullName
	}
	writeJSON(w, http.StatusOK, resp)
}

func (s *Server) issueAndRespond(w http.ResponseWriter, user *db.User) {
	token, exp, err := s.deps.Issuer.Issue(user.ID, user.Email, user.Role)
	if err != nil {
		s.log.Error("issue token", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not issue token")
		return
	}
	resp := authResponse{
		AccessToken: token,
		TokenType:   "Bearer",
		ExpiresAt:   exp.Format(time.RFC3339),
		UserID:      user.ID,
		Email:       user.Email,
		Role:        user.Role,
	}
	if user.FullName != nil {
		resp.FullName = *user.FullName
	}
	writeJSON(w, http.StatusOK, resp)
}

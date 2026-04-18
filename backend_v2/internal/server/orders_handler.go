package server

import (
	"encoding/json"
	"errors"
	"net/http"
	"strconv"

	"github.com/go-chi/chi/v5"

	"skincare/backend-v2/internal/auth"
	"skincare/backend-v2/internal/db"
)

type orderItemPayload struct {
	SKU         string  `json:"sku"`
	ProductName string  `json:"product_name"`
	Quantity    int     `json:"quantity"`
	Price       float64 `json:"price"`
}

type createOrderRequest struct {
	Channel string             `json:"channel"`
	Items   []orderItemPayload `json:"items"`
}

type orderView struct {
	ID          int             `json:"id"`
	OrderNumber string          `json:"order_number"`
	UserID      string          `json:"user_id,omitempty"`
	UserEmail   string          `json:"user_email,omitempty"`
	Status      string          `json:"status"`
	Total       *float64        `json:"total,omitempty"`
	Channel     string          `json:"channel,omitempty"`
	Items       []db.OrderItem  `json:"items"`
	ItemsCount  int             `json:"items_count"`
	WCOrderID   *int            `json:"wc_order_id,omitempty"`
	CreatedAt   string          `json:"created_at"`
}

func orderToView(o db.Order) orderView {
	v := orderView{
		ID:          o.ID,
		OrderNumber: formatOrderNumber(o.ID),
		UserID:      o.UserID,
		Status:      o.Status,
		Total:       o.Total,
		Channel:     o.Channel,
		Items:       o.Items,
		ItemsCount:  len(o.Items),
		WCOrderID:   o.WCOrderID,
		CreatedAt:   o.CreatedAt.Format("2006-01-02T15:04:05Z07:00"),
	}
	if o.UserEmail != nil {
		v.UserEmail = *o.UserEmail
	}
	return v
}

func formatOrderNumber(id int) string {
	return "SK" + padInt(id, 6)
}

func padInt(n, width int) string {
	s := strconv.Itoa(n)
	for len(s) < width {
		s = "0" + s
	}
	return s
}

// POST /orders
func (s *Server) handleCreateOrder(w http.ResponseWriter, r *http.Request) {
	p := auth.PrincipalFrom(r.Context())
	if p == nil {
		writeError(w, http.StatusUnauthorized, "unauthenticated", "missing auth")
		return
	}

	var req createOrderRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "invalid JSON body")
		return
	}
	if req.Channel == "" {
		req.Channel = "web"
	}
	if len(req.Items) == 0 {
		writeError(w, http.StatusBadRequest, "bad_request", "at least one item required")
		return
	}

	items := make([]db.OrderItem, 0, len(req.Items))
	var total float64
	for _, it := range req.Items {
		if it.Quantity <= 0 {
			writeError(w, http.StatusBadRequest, "bad_request", "item quantity must be positive")
			return
		}
		items = append(items, db.OrderItem{
			SKU:         it.SKU,
			ProductName: it.ProductName,
			Quantity:    it.Quantity,
			Price:       it.Price,
		})
		total += it.Price * float64(it.Quantity)
	}

	id, createdAt, err := s.deps.Orders.Insert(r.Context(), &db.InsertOrderInput{
		UserID:  p.UserID,
		Channel: req.Channel,
		Items:   items,
		Total:   &total,
	})
	if err != nil {
		s.log.Error("insert order", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not create order")
		return
	}

	writeJSON(w, http.StatusCreated, orderView{
		ID:          id,
		OrderNumber: formatOrderNumber(id),
		Status:      "created",
		Total:       &total,
		Channel:     req.Channel,
		Items:       items,
		ItemsCount:  len(items),
		CreatedAt:   createdAt.Format("2006-01-02T15:04:05Z07:00"),
	})
}

// GET /orders
func (s *Server) handleListOrders(w http.ResponseWriter, r *http.Request) {
	p := auth.PrincipalFrom(r.Context())
	if p == nil {
		writeError(w, http.StatusUnauthorized, "unauthenticated", "missing auth")
		return
	}

	orders, err := s.deps.Orders.ListByUser(r.Context(), p.UserID)
	if err != nil {
		s.log.Error("list orders", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not load orders")
		return
	}
	out := make([]orderView, 0, len(orders))
	for _, o := range orders {
		out = append(out, orderToView(o))
	}
	writeJSON(w, http.StatusOK, map[string]any{"orders": out})
}

// GET /orders/{id}
func (s *Server) handleGetOrder(w http.ResponseWriter, r *http.Request) {
	p := auth.PrincipalFrom(r.Context())
	if p == nil {
		writeError(w, http.StatusUnauthorized, "unauthenticated", "missing auth")
		return
	}
	idStr := chi.URLParam(r, "id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "invalid order id")
		return
	}
	order, err := s.deps.Orders.GetByID(r.Context(), id)
	if err != nil {
		if errors.Is(err, db.ErrOrderNotFound) {
			writeError(w, http.StatusNotFound, "not_found", "order not found")
			return
		}
		s.log.Error("get order", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "lookup failed")
		return
	}
	if order.UserID != p.UserID && !p.IsAdmin() {
		writeError(w, http.StatusForbidden, "forbidden", "not your order")
		return
	}
	writeJSON(w, http.StatusOK, orderToView(*order))
}

function salesPage() {
  return {
    q: '',
    cart: [],
    products: [],
    customerName: '',
    paymentMethod: 'cash',
    processing: false,
    showConfirm: false,
    lastReceiptId: null,

    init() {
        // Load products from an injected global or try a fallback API
        if (window.INIT_PRODUCTS) {
          this.products = window.INIT_PRODUCTS;
        } else {
          try {
            fetch('/api/products')
              .then(r => r.json())
              .then(data => { this.products = data; })
              .catch(() => { this.products = []; });
          } catch (e) {
            this.products = [];
          }
        }
    },

    filtered() {
      if (!this.q) return this.products;
      const query = this.q.toLowerCase();
      return this.products.filter(p => 
        p.name.toLowerCase().includes(query) || 
        (p.sku && p.sku.toLowerCase().includes(query))
      );
    },

    getMaxStock(productId) {
      const product = this.products.find(p => p.id === productId);
      return product ? product.stock : 0;
    },

    add(product) {
      const existing = this.cart.find(it => it.id === product.id);
      if (existing) {
        if (existing.qty < product.stock) {
          existing.qty++;
        }
      } else {
        this.cart.push({
          id: product.id,
          name: product.name,
          price: product.price,
          qty: 1
        });
      }
    },

    remove(idx) {
      this.cart.splice(idx, 1);
    },

    clearCart() {
      this.cart = [];
      this.customerName = '';
      this.paymentMethod = 'cash';
    },

    total() {
      return this.cart.reduce((sum, item) => sum + item.price * item.qty, 0);
    },

    async checkout() {
      if (this.processing) return;
      
      this.processing = true;
      try {
        const response = await fetch('/api/checkout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            items: this.cart,
            customer: this.customerName,
            payment_method: this.paymentMethod
          })
        });

        if (!response.ok) {
          throw new Error('Error al procesar la venta');
        }

        const data = await response.json();
        this.lastReceiptId = data.receipt_id;
        this.showConfirm = true;
        this.clearCart();

      } catch (err) {
        alert('Error al procesar la venta: ' + err.message);
      } finally {
        this.processing = false;
      }
    }
  };
}
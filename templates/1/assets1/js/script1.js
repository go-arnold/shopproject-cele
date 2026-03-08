// Products data with enhanced information
        const products = [
            {
                id: 1,
                name: "iPhone 15 Pro Max",
                description: "Smartphone premium avec puce A17 Pro, appareil photo 48MP et écran Super Retina XDR",
                price: 1299,
                category: "smartphone",
                image: "assets/images/i15.jpg",
                badge: "Nouveau",
                features: ["5G", "A17 Pro", "48MP", "1TB"],
                rating: 4.8,
                reviews: 256
            },
            {
                id: 2,
                name: "MacBook Pro 16\"",
                description: "Ordinateur portable avec puce M3 Pro, écran Liquid Retina XDR et 32GB de RAM unifié",
                price: 2799,
                category: "ordinateur",
                image: "assets/images/mac16.jpg",
                badge: "Pro",
                features: ["M3 Pro", "32GB RAM", "1TB SSD", "16\""],
                rating: 4.9,
                reviews: 189
            },
            {
                id: 3,
                name: "AirPods Pro 3",
                description: "Écouteurs sans fil avec réduction de bruit adaptative et audio spatial personnalisé",
                price: 299,
                category: "audio",
                image: "assets/images/air3.jpg",
                badge: "Populaire",
                features: ["ANC", "30h", "USB-C", "Spatial"],
                rating: 4.7,
                reviews: 423
            },
            {
                id: 4,
                name: "Apple Watch Ultra 2",
                description: "Montre connectée sportive avec GPS précis, écran Retina toujours actif et étanchéité 100m",
                price: 899,
                category: "montre",
                image: "assets/images/watch.jpg",
                badge: "Sport",
                features: ["GPS", "100m", "49mm", "Titanium"],
                rating: 4.6,
                reviews: 167
            },
            {
                id: 5,
                name: "iPad Pro 12.9\" M4",
                description: "Tablette professionnelle avec puce M4, écran Liquid Retina XDR et support Apple Pencil Pro",
                price: 1399,
                category: "tablette",
                image: "assets/images/iPad.jpg",
                badge: "Pro",
                features: ["M4", "12.9\"", "XDR", "2TB"],
                rating: 4.8,
                reviews: 134
            },
            {
                id: 6,
                name: "Sony WH-1000XM5",
                description: "Casque sans fil premium avec réduction de bruit leader du marché et 30h d'autonomie",
                price: 399,
                category: "audio",
                image: "assets/images/casque.jpg",
                badge: "Promo",
                features: ["ANC", "30h", "Hi-Res", "Multipoint"],
                rating: 4.7,
                reviews: 298
            },
            {
                id: 7,
                name: "Samsung Galaxy S24 Ultra",
                description: "Smartphone Android flagship avec S Pen intégré, zoom 100x et écran Dynamic AMOLED",
                price: 1399,
                category: "smartphone",
                image: "assets/images/s24.jpg",
                badge: "Android",
                features: ["S Pen", "200MP", "100x Zoom", "6.8\""],
                rating: 4.6,
                reviews: 201
            },
            {
                id: 8,
                name: "Surface Pro 9",
                description: "Tablette 2-en-1 Windows avec processeur Intel i7, écran tactile 13\" et Type Cover inclus",
                price: 1599,
                category: "ordinateur",
                image: "assets/images/surface.jpg",
                badge: "2-en-1",
                features: ["i7", "16GB", "13\"", "Windows"],
                rating: 4.5,
                reviews: 156
            },
            {
                id: 9,
                name: "Google Pixel 8 Pro",
                description: "Smartphone Google avec IA avancée, appareil photo computationnel et 7 ans de mises à jour",
                price: 999,
                category: "smartphone",
                image: "assets/images/pixel8.jpg",
                badge: "IA",
                features: ["Tensor G3", "IA", "50MP", "7 ans MAJ"],
                rating: 4.4,
                reviews: 178
            },
            {
                id: 10,
                name: "JBL Charge 5",
                description: "Enceinte Bluetooth portable avec son JBL Pro, étanchéité IP67 et powerbank intégré",
                price: 179,
                category: "audio",
                image: "assets/images/jbl.jpg",
                badge: "Outdoor",
                features: ["IP67", "20h", "Powerbank", "JBL Pro"],
                rating: 4.5,
                reviews: 512
            },
            {
                id: 11,
                name: "Dell XPS 15",
                description: "Ultrabook premium avec écran OLED 4K, processeur Intel i9 et carte graphique RTX 4070",
                price: 2299,
                category: "ordinateur",
                image: "assets/images/dell1.jpg",
                badge: "OLED",
                features: ["i9", "RTX 4070", "OLED 4K", "32GB"],
                rating: 4.7,
                reviews: 143
            },
            {
                id: 12,
                name: "Fitbit Sense 2",
                description: "Montre de santé connectée avec capteurs avancés, GPS et suivi du stress et du sommeil",
                price: 299,
                category: "montre",
                image: "assets/images/connectedW.jpg",
                badge: "Santé",
                features: ["ECG", "SpO2", "GPS", "6 jours"],
                rating: 4.3,
                reviews: 234
            }
        ];

        // Filter and search state
        let filteredProducts = [...products];
        let activeFilters = {
            category: 'all',
            price: 'all',
            search: ''
        };

        // Cart state
        let cart = [];

        // Testimonials data
        const testimonials = [
            {
                id: 1,
                name: "Bashokwire Alain",
                avatar: "M",
                date: "Il y a 2 jours",
                rating: 5,
                message: "Livraison ultra rapide ! J'ai reçu mon iPhone 15 Pro Max en moins de 24h. L'emballage était parfait et le produit correspond exactement à la description. Service client au top ! 👍",
                product: {
                    name: "iPhone 15 Pro Max",
                    price: "1299$",
                    emoji: "📱"
                },
                badge: "Acheteur vérifié"
            },
            {
                id: 2,
                name: "Eric Murhabazi",
                avatar: "T",
                date: "Il y a 5 jours",
                rating: 5,
                message: "Excellent choix pour mon travail ! Le MacBook Pro avec la puce M3 est une vraie révolution. Performances exceptionnelles et autonomie remarquable. Je recommande vivement CeleBobo !",
                product: {
                    name: "MacBook Pro 16\"",
                    price: "2799$",
                    emoji: "💻"
                },
                badge: "Client Premium"
            },
            {
                id: 3,
                name: "Mugisho Mulume",
                avatar: "S",
                date: "Il y a 1 semaine",
                rating: 4,
                message: "Les AirPods Pro 3 sont fantastiques ! La réduction de bruit est impressionnante et le son est cristallin. Petit bémol sur le prix mais la qualité est au rendez-vous.",
                product: {
                    name: "AirPods Pro 3",
                    price: "299$",
                    emoji: "🎧"
                },
                badge: "Acheteur vérifié"
            },
            {
                id: 4,
                name: "Patrick Cibembe",
                avatar: "L",
                date: "Il y a 1 semaine",
                rating: 5,
                message: "Ma Apple Watch Ultra 2 est parfaite pour mes entraînements ! GPS précis, résistance à l'eau au top, et l'écran reste lisible même en plein soleil. Bravo CeleBobo pour ce service !",
                product: {
                    name: "Apple Watch Ultra 2",
                    price: "899$",
                    emoji: "⌚"
                },
                badge: "Acheteur vérifié"
            },
            {
                id: 5,
                name: "Amina Cikuru",
                avatar: "E",
                date: "Il y a 2 semaines",
                rating: 5,
                message: "iPad Pro M4 reçu en parfait état ! Idéal pour mes créations graphiques. L'écran XDR est sublime et les performances sont bluffantes. Livraison soignée comme toujours chez CeleBobo.",
                product: {
                    name: "iPad Pro 12.9\" M4",
                    price: "1399$",
                    emoji: "📱"
                },
                badge: "Client Premium"
            },
            {
                id: 6,
                name: "Fadhili Fundiko",
                avatar: "A",
                date: "Il y a 3 semaines",
                rating: 4,
                message: "Sony WH-1000XM5 au top ! Le casque est confortable pour de longues sessions d'écoute. La réduction de bruit active est efficace. Rapport qualité-prix correct.",
                product: {
                    name: "Sony WH-1000XM5",
                    price: "399$",
                    emoji: "🎧"
                },
                badge: "Acheteur vérifié"
            }
        ];

        // Chat state and functionality
        let userMessages = [];
        let currentEditingId = null;
        let selectedImage = null;

        // Enhanced chat messages with IDs for editing/deleting
        const initialChatMessages = [
            {
                id: 'support-1',
                type: 'support',
                name: 'Sarah',
                avatar: 'S',
                message: 'Bonjour ! Je suis Sarah de l\'équipe CeleBobo. Comment puis-je vous aider aujourd\'hui ? 😊',
                time: '14:32',
                timestamp: Date.now() - 300000
            },
            {
                id: 'user-1',
                type: 'user',
                name: 'Client',
                avatar: 'C',
                message: 'Salut ! Je voudrais savoir si l\'iPhone 15 Pro Max est disponible en 1TB ?',
                time: '14:33',
                timestamp: Date.now() - 240000
            },
            {
                id: 'support-2',
                type: 'support',
                name: 'Sarah',
                avatar: 'S',
                message: 'Excellente question ! Oui, nous avons le modèle 1TB en stock dans toutes les couleurs. Souhaitez-vous que je vérifie la disponibilité pour une couleur spécifique ?',
                time: '14:33',
                timestamp: Date.now() - 180000
            },
            {
                id: 'user-2',
                type: 'user',
                name: 'Client',
                avatar: 'C',
                message: 'Parfait ! En Titanium Naturel si possible. Et pour la livraison, c\'est rapide ?',
                time: '14:34',
                timestamp: Date.now() - 120000
            },
            {
                id: 'support-3',
                type: 'support',
                name: 'Sarah',
                avatar: 'S',
                message: 'Super choix ! 👍 Le Titanium Naturel 1TB est disponible. Livraison express gratuite sous 24h si vous commandez avant 16h. Voulez-vous que je vous aide à finaliser votre commande ?',
                time: '14:35',
                timestamp: Date.now() - 60000
            }
        ];

        // Copy initial messages to user messages for editing
        userMessages = [...initialChatMessages];

        // Auto-resize textarea
        function autoResize(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        }

        // Handle enter key press
        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        // Handle image upload
        function handleImageUpload(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    selectedImage = {
                        src: e.target.result,
                        name: file.name,
                        size: file.size
                    };
                    showImagePreview();
                };
                reader.readAsDataURL(file);
            }
        }

        // Show image preview
        function showImagePreview() {
            const preview = document.getElementById('image-preview');
            const previewImg = document.getElementById('preview-image');
            
            if (selectedImage) {
                previewImg.src = selectedImage.src;
                preview.classList.add('show');
            }
        }

        // Remove image preview
        function removeImagePreview() {
            selectedImage = null;
            const preview = document.getElementById('image-preview');
            preview.classList.remove('show');
            document.getElementById('image-upload').value = '';
        }

        // Send message
        function sendMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            
            if (!message && !selectedImage) return;
            
            const now = new Date();
            const timeString = now.getHours().toString().padStart(2, '0') + ':' + 
                              now.getMinutes().toString().padStart(2, '0');
            
            const newMessage = {
                id: 'user-' + Date.now(),
                type: 'user',
                name: 'Vous',
                avatar: 'V',
                message: message || '📷 Image partagée',
                time: timeString,
                timestamp: Date.now(),
                image: selectedImage ? selectedImage.src : null,
                editable: true
            };
            
            userMessages.push(newMessage);
            renderMessages();
            
            // Clear input and image
            input.value = '';
            input.style.height = 'auto';
            removeImagePreview();
            
            // Scroll to bottom
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            // Simulate support response
            setTimeout(simulateSupportResponse, 2000);
        }

        // Simulate support response
        function simulateSupportResponse() {
            const responses = [
                'Merci pour votre message ! Je vais vérifier cela pour vous. 👍',
                'C\'est une excellente question ! Laissez-moi vous aider avec ça.',
                'Je comprends parfaitement votre demande. Voici ce que je peux vous proposer...',
                'Parfait ! Je vais traiter votre demande immédiatement.',
                'Merci pour cette information. Je reviens vers vous dans quelques instants.'
            ];
            
            const randomResponse = responses[Math.floor(Math.random() * responses.length)];
            
            const now = new Date();
            const timeString = now.getHours().toString().padStart(2, '0') + ':' + 
                              now.getMinutes().toString().padStart(2, '0');
            
            const supportMessage = {
                id: 'support-' + Date.now(),
                type: 'support',
                name: 'Sarah',
                avatar: 'S',
                message: randomResponse,
                time: timeString,
                timestamp: Date.now()
            };
            
            userMessages.push(supportMessage);
            renderMessages();
            
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        // Edit message
        function editMessage(messageId) {
            const message = userMessages.find(m => m.id === messageId);
            if (!message || !message.editable) return;
            
            currentEditingId = messageId;
            renderMessages();
        }

        // Save edited message
        function saveEdit(messageId) {
            const input = document.querySelector(`#edit-input-${messageId}`);
            const message = userMessages.find(m => m.id === messageId);
            
            if (input && message) {
                const newText = input.value.trim();
                if (newText) {
                    message.message = newText;
                    message.edited = true;
                }
            }
            
            currentEditingId = null;
            renderMessages();
        }

        // Cancel edit
        function cancelEdit() {
            currentEditingId = null;
            renderMessages();
        }

        // Delete message
        function deleteMessage(messageId) {
            if (confirm('Êtes-vous sûr de vouloir supprimer ce message ?')) {
                userMessages = userMessages.filter(m => m.id !== messageId);
                renderMessages();
            }
        }

        // Show image in modal
        function showImageModal(imageSrc) {
            const modal = document.getElementById('image-modal');
            const modalImage = document.getElementById('modal-image');
            modalImage.src = imageSrc;
            modal.classList.add('show');
        }

        // Close image modal
        function closeImageModal() {
            const modal = document.getElementById('image-modal');
            modal.classList.remove('show');
        }

        // Render all messages
        function renderMessages() {
            const chatContainer = document.getElementById('chat-messages');
            if (!chatContainer) return;
            
            chatContainer.innerHTML = '';
            
            userMessages.forEach((message) => {
                const isEditing = currentEditingId === message.id;
                const canEdit = message.editable && message.type === 'user';
                
                const messageElement = document.createElement('div');
                messageElement.className = `chat-message ${message.type}`;
                messageElement.style.opacity = '1';
                
                let imageHtml = '';
                if (message.image) {
                    imageHtml = `<img src="${message.image}" alt="Image partagée" class="message-image" onclick="showImageModal('${message.image}')">`;
                }
                
                let actionsHtml = '';
                if (canEdit) {
                    actionsHtml = `
                        <div class="message-actions">
                            <button class="action-btn edit-btn" onclick="editMessage('${message.id}')" title="Modifier">✏️</button>
                            <button class="action-btn delete-btn" onclick="deleteMessage('${message.id}')" title="Supprimer">🗑️</button>
                        </div>
                    `;
                }
                
                let editHtml = '';
                if (isEditing) {
                    editHtml = `
                        <input type="text" class="edit-input" id="edit-input-${message.id}" value="${message.message}">
                        <div class="edit-actions">
                            <button class="save-btn" onclick="saveEdit('${message.id}')">Sauver</button>
                            <button class="cancel-btn" onclick="cancelEdit()">Annuler</button>
                        </div>
                    `;
                }
                
                const editedStatus = message.edited ? '<span class="message-status">(modifié)</span>' : '';
                
                messageElement.innerHTML = `
                    <div class="message-avatar ${message.type}">
                        ${message.avatar}
                    </div>
                    <div class="message-content">
                        ${actionsHtml}
                        <div class="message-bubble ${isEditing ? 'editing' : ''}">
                            ${isEditing ? '' : message.message}
                        </div>
                        ${imageHtml}
                        ${editHtml}
                        <div class="message-time">
                            ${message.time} ${editedStatus}
                        </div>
                    </div>
                `;
                
                chatContainer.appendChild(messageElement);
            });
            
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        // Load chat messages with animation (modified)
        function loadChatMessages() {
            // Just render the initial messages
            renderMessages();
        } 
        const chatMessages = [
            {
                type: 'support',
                name: 'Sarah',
                avatar: 'S',
                message: 'Bonjour ! Je suis Sarah de l\'équipe CeleBobo. Comment puis-je vous aider aujourd\'hui ? 😊',
                time: '14:32'
            },
            {
                type: 'user',
                name: 'Client',
                avatar: 'C',
                message: 'Salut ! Je voudrais savoir si l\'iPhone 15 Pro Max est disponible en 1TB ?',
                time: '14:33'
            },
            {
                type: 'support',
                name: 'Sarah',
                avatar: 'S',
                message: 'Excellente question ! Oui, nous avons le modèle 1TB en stock dans toutes les couleurs. Souhaitez-vous que je vérifie la disponibilité pour une couleur spécifique ?',
                time: '14:33'
            },
            {
                type: 'user',
                name: 'Client',
                avatar: 'C',
                message: 'Parfait ! En Titanium Naturel si possible. Et pour la livraison, c\'est rapide ?',
                time: '14:34'
            },
            {
                type: 'support',
                name: 'Sarah',
                avatar: 'S',
                message: 'Super choix ! 👍 Le Titanium Naturel 1TB est disponible. Livraison express gratuite sous 24h si vous commandez avant 16h. Voulez-vous que je vous aide à finaliser votre commande ?',
                time: '14:35'
            },
            {
                type: 'user',
                name: 'Client',
                avatar: 'C',
                message: 'Génial ! Oui je veux bien, et est-ce que vous avez des promotions en ce moment ?',
                time: '14:36'
            },
            {
                type: 'support',
                name: 'Sarah',
                avatar: 'S',
                message: 'Bonne nouvelle ! Nous avons une offre spéciale : 10% de remise + AirPods Pro offerts pour tout achat d\'iPhone 15 Pro Max. L\'offre est valable jusqu\'à dimanche ! 🎉',
                time: '14:37'
            }
        ];

        // Load testimonials
        function loadTestimonials() {
            const grid = document.getElementById('testimonials-grid');
            if (!grid) return;
            
            grid.innerHTML = '';
            
            testimonials.forEach((testimonial, index) => {
                const delay = index * 0.1;
                const badgeClass = testimonial.badge.includes('Premium') ? 'premium' : 'verified';
                
                const testimonialCard = `
                    <div class="testimonial-card fade-in" style="animation-delay: ${delay}s">
                        <div class="testimonial-badge ${badgeClass}">${testimonial.badge}</div>
                        <div class="testimonial-header">
                            <div class="testimonial-avatar">${testimonial.avatar}</div>
                            <div class="testimonial-info">
                                <h4>${testimonial.name}</h4>
                                <div class="testimonial-date">${testimonial.date}</div>
                            </div>
                        </div>
                        <div class="testimonial-rating">
                            ${Array(testimonial.rating).fill().map(() => '<span class="star">★</span>').join('')}
                            ${Array(5 - testimonial.rating).fill().map(() => '<span class="star" style="color: #333;">★</span>').join('')}
                        </div>
                        <div class="testimonial-message">${testimonial.message}</div>
                        <div class="testimonial-product">
                            <div class="testimonial-product-emoji">${testimonial.product.emoji}</div>
                            <div class="testimonial-product-info">
                                <div class="testimonial-product-name">${testimonial.product.name}</div>
                                <div class="testimonial-product-price">${testimonial.product.price}</div>
                            </div>
                        </div>
                    </div>
                `;
                grid.innerHTML += testimonialCard;
            });
        }

        // Load chat messages with animation
        function loadChatMessages() {
            const chatContainer = document.getElementById('chat-messages');
            if (!chatContainer) return;
            
            chatContainer.innerHTML = '';
            
            chatMessages.forEach((message, index) => {
                setTimeout(() => {
                    const messageElement = `
                        <div class="chat-message ${message.type}" style="animation-delay: 0s">
                            <div class="message-avatar ${message.type}">
                                ${message.avatar}
                            </div>
                            <div class="message-content">
                                <div class="message-bubble">
                                    ${message.message}
                                </div>
                                <div class="message-time">${message.time}</div>
                            </div>
                        </div>
                    `;
                    chatContainer.innerHTML += messageElement;
                    
                    // Auto scroll to bottom
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                    
                    // Show typing indicator for next message (except last one)
                    if (index < chatMessages.length - 1 && message.type === 'user') {
                        setTimeout(() => {
                            const typingIndicator = `
                                <div class="typing-indicator show">
                                    <div class="message-avatar support">S</div>
                                    <div class="typing-dots">
                                        <div class="typing-dot"></div>
                                        <div class="typing-dot"></div>
                                        <div class="typing-dot"></div>
                                    </div>
                                </div>
                            `;
                            chatContainer.innerHTML += typingIndicator;
                            chatContainer.scrollTop = chatContainer.scrollHeight;
                            
                            // Remove typing indicator before next message
                            setTimeout(() => {
                                const indicator = chatContainer.querySelector('.typing-indicator');
                                if (indicator) indicator.remove();
                            }, 1500);
                        }, 500);
                    }
                }, index * 2000);
            });
        }

        // Initialize testimonials and chat when page loads
        document.addEventListener('DOMContentLoaded', function() {
            loadProducts();
            setupCategoryFilters();
            loadTestimonials();
            setupScrollAnimations();
            
            // Start chat simulation after a delay
            setTimeout(loadChatMessages, 1000);
        });

        // Load and display products
        function loadProducts() {
            const grid = document.getElementById('products-grid');
            const noResults = document.getElementById('no-results');
            
            if (filteredProducts.length === 0) {
                grid.style.display = 'none';
                noResults.style.display = 'block';
                return;
            }
            
            grid.style.display = 'grid';
            noResults.style.display = 'none';
            grid.innerHTML = '';
            
            filteredProducts.forEach(product => {
                const productCard = `
                    <div class="product-card fade-in" data-category="${product.category}">
                        <div class="product-image">
                            <span class="product-emoji"><img src="${product.image}" alt="image of ${product.name}" style="width:100%; height:auto;"></span>
                            <span class="product-badge">${product.current_badge}</span>
                        </div>
                        <div class="product-info">
                            <div class="product-category">${getCategoryName(product.category)}</div>
                            <h3 class="product-title">${product.name}</h3>
                            <p class="product-description">${product.description}</p>
                            <div class="product-features">
                                ${product.features.map(feature => `<span class="feature-tag">${feature}</span>`).join('')}
                            </div>
                            <div class="product-price-row">
                                <div class="product-price">${product.price}$</div>
                                <div class="product-rating">
                                    <span class="stars">${'★'.repeat(Math.floor(product.rating))}${product.rating % 1 >= 0.5 ? '☆' : ''}</span>
                                    <span>${product.rating} (${product.reviews})</span>
                                </div>
                            </div>
                            <button class="add-to-cart" onclick="addToCart(${product.id})">
                                Ajouter au panier
                            </button>
                        </div>
                    </div>
                `;
                grid.innerHTML += productCard;
            });
        }

        // Get category display name
        function getCategoryName(category) {
            const names = {
                'smartphone': 'Smartphones',
                'ordinateur': 'Ordinateurs',
                'tablette': 'Tablettes',
                'audio': 'Audio',
                'montre': 'Montres connectées'
            };
            return names[category] || category;
        }

        // Setup category filter buttons
        function setupCategoryFilters() {
            const categories = [...new Set(products.map(p => p.category))];
            const filterContainer = document.getElementById('category-filters');
            
            categories.forEach(category => {
                const button = document.createElement('button');
                button.className = 'filter-btn';
                button.textContent = getCategoryName(category);
                button.dataset.category = category;
                button.onclick = () => setActiveFilter('category', category);
                filterContainer.appendChild(button);
            });
        }

        // Set active filter
        function setActiveFilter(type, value) {
            activeFilters[type] = value;
            
            // Update UI
            if (type === 'category') {
                document.querySelectorAll('#category-filters .filter-btn').forEach(btn => {
                    btn.classList.toggle('active', btn.dataset.category === value || (value === 'all' && btn.textContent === 'Tout'));
                });
            }
            
            filterProducts();
        }

        // Filter products based on search and filters
        function filterProducts() {
            const searchTerm = document.getElementById('search-input').value.toLowerCase();
            const priceRange = document.getElementById('price-filter').value;
            
            activeFilters.search = searchTerm;
            activeFilters.price = priceRange;
            
            filteredProducts = products.filter(product => {
                // Search filter
                const matchesSearch = !searchTerm || 
                    product.name.toLowerCase().includes(searchTerm) ||
                    product.description.toLowerCase().includes(searchTerm) ||
                    product.category.toLowerCase().includes(searchTerm) ||
                    product.features.some(feature => feature.toLowerCase().includes(searchTerm));
                
                // Category filter
                const matchesCategory = activeFilters.category === 'all' || product.category === activeFilters.category;
                
                // Price filter
                let matchesPrice = true;
                if (priceRange !== 'all') {
                    const [min, max] = priceRange.split('-').map(p => parseInt(p.replace('+', '')) || Infinity);
                    matchesPrice = product.price >= min && (max === Infinity || product.price <= max);
                }
                
                return matchesSearch && matchesCategory && matchesPrice;
            });
            
            loadProducts();
        }

        // Clear all filters
        function clearFilters() {
            activeFilters = { category: 'all', price: 'all', search: '' };
            document.getElementById('search-input').value = '';
            document.getElementById('price-filter').value = 'all';
            document.querySelectorAll('#category-filters .filter-btn').forEach((btn, index) => {
                btn.classList.toggle('active', index === 0);
            });
            filteredProducts = [...products];
            loadProducts();
        }

        // Mobile menu functions
        function toggleMobileMenu() {
            const menu = document.getElementById('mobile-menu');
            menu.classList.toggle('open');
        }

        function closeMobileMenu() {
            const menu = document.getElementById('mobile-menu');
            menu.classList.remove('open');
        }

        // Cart functions
        function addToCart(productId) {
            const product = products.find(p => p.id === productId);
            const existingItem = cart.find(item => item.id === productId);
            
            if (existingItem) {
                existingItem.quantity += 1;
            } else {
                cart.push({ ...product, quantity: 1 });
            }
            
            updateCartUI();
            
            // Visual feedback
            const button = event.target;
            const originalText = button.textContent;
            button.textContent = 'Ajouté!';
            button.style.background = '#640D5F';
            setTimeout(() => {
                button.textContent = originalText;
                button.style.background = '';
            }, 1000);
        }

        function removeFromCart(productId) {
            cart = cart.filter(item => item.id !== productId);
            updateCartUI();
        }

        function updateQuantity(productId, newQuantity) {
            const item = cart.find(item => item.id === productId);
            if (item) {
                if (newQuantity <= 0) {
                    removeFromCart(productId);
                } else {
                    item.quantity = newQuantity;
                    updateCartUI();
                }
            }
        }

        function updateCartUI() {
            const cartCount = document.getElementById('cart-count');
            const cartText = document.getElementById('cart-text');
            const cartItems = document.getElementById('cart-items');
            const cartTotal = document.getElementById('cart-total');
            
            // Update cart count
            const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
            cartCount.textContent = totalItems;
            cartCount.style.display = totalItems > 0 ? 'flex' : 'none';
            
            // Update cart text for mobile
            if (window.innerWidth <= 768) {
                cartText.style.display = 'none';
            }
            
            // Update cart items
            if (cart.length === 0) {
                cartItems.innerHTML = '<p style="text-align: center; color: #666; padding: 2rem;">Votre panier est vide</p>';
            } else {
                cartItems.innerHTML = cart.map(item => `
                    <div class="cart-item">
                        <div class="cart-item-info">
                            <div class="cart-item-title">${item.name}</div>
                            <div class="cart-item-price">${item.price}$ × ${item.quantity}</div>
                        </div>
                        <div class="cart-item-controls">
                            <button class="qty-btn" onclick="updateQuantity(${item.id}, ${item.quantity - 1})">-</button>
                            <span style="min-width: 20px; text-align: center;">${item.quantity}</span>
                            <button class="qty-btn" onclick="updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
                            <button class="remove-btn" onclick="removeFromCart(${item.id})">×</button>
                        </div>
                    </div>
                `).join('');
            }
            
            // Update total
            const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            cartTotal.textContent = `${total}$`;
        }

        function toggleCart() {
            const sidebar = document.getElementById('cart-sidebar');
            const overlay = document.getElementById('cart-overlay');
            
            sidebar.classList.toggle('open');
            overlay.classList.toggle('active');
        }

        function closeCart() {
            const sidebar = document.getElementById('cart-sidebar');
            const overlay = document.getElementById('cart-overlay');
            
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        }

        function checkout() {
            if (cart.length === 0) {
                alert('Votre panier est vide !');
                return;
            }
            
            const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            alert(`Commande validée !\nTotal: ${total}$\nMerci pour votre achat !`);
            
            cart = [];
            updateCartUI();
            closeCart();
        }

        // Contact form
        function submitContact(event) {
            event.preventDefault();
            alert('Message envoyé avec succès ! Nous vous répondrons dans les plus brefs délais.');
            event.target.reset();
        }

        // Smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
                closeMobileMenu();
            });
        });

        // Setup scroll animations
        function setupScrollAnimations() {
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('fade-in');
                    }
                });
            }, observerOptions);
            
            // Observe elements for animation
            setTimeout(() => {
                document.querySelectorAll('.product-card, .about-text, .testimonial-card').forEach(el => {
                    observer.observe(el);
                });
            }, 100);
        }

        // Handle window resize
        window.addEventListener('resize', () => {
            const cartText = document.getElementById('cart-text');
            if (window.innerWidth <= 768) {
                cartText.style.display = 'none';
            } else {
                cartText.style.display = 'inline';
            }
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', function(event) {
            const menu = document.getElementById('mobile-menu');
            const menuToggle = document.querySelector('.menu-toggle');
            
            if (menu.classList.contains('open') && 
                !menu.contains(event.target) && 
                !menuToggle.contains(event.target)) {
                closeMobileMenu();
            }
        });
   

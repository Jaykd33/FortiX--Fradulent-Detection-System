"""
Graph Neural Network service for fraud detection.
Constructs transaction graphs and generates entity embeddings.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
import logging
from pathlib import Path
import pickle

logger = logging.getLogger("fortix.gnn")


class GNNService:
    """
    Lightweight GNN service for fraud detection.
    Uses graph structure to generate contextual embeddings.
    """
    
    def __init__(self, embedding_dim: int = 16):
        self.embedding_dim = embedding_dim
        self.node_embeddings: Dict[str, np.ndarray] = {}
        self.available = False
        self.model_path = Path("ml_models/gnn_embeddings.pkl")
        
        # Check if PyTorch is available
        try:
            import torch
            import torch.nn as nn
            self.torch_available = True
            self.torch = torch
            self.nn = nn
        except ImportError:
            self.torch_available = False
            logger.warning("PyTorch not available; using heuristic-based GNN")
    
    def build_transaction_graph(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Build a transaction graph from DataFrame.
        
        Nodes: Users, Merchants, Devices
        Edges: Transactions with attributes (amount, time, distance)
        
        Returns:
            Dictionary with node indices, edge lists, and edge features
        """
        graph = {
            "user_nodes": {},
            "merchant_nodes": {},
            "device_nodes": {},
            "edges": [],
            "edge_features": [],
        }
        
        # Get columns
        user_col = None
        merchant_col = None
        device_col = None
        amount_col = None
        time_col = None
        distance_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if "user_id" in col_lower or "sender" in col_lower:
                user_col = col
            elif "receiver" in col_lower or "merchant" in col_lower:
                merchant_col = col
            elif "device" in col_lower:
                device_col = col
            elif "amount" in col_lower and "transaction" in col_lower:
                amount_col = col
            elif "timestamp" in col_lower or "time" in col_lower:
                time_col = col
            elif "distance" in col_lower:
                distance_col = col
        
        if not user_col or not merchant_col:
            logger.warning("Missing user or merchant columns; using defaults")
            user_col = user_col or "User_ID"
            merchant_col = merchant_col or "Receiver_ID"
        
        # Create node mappings
        users = df[user_col].astype(str).unique()
        merchants = df[merchant_col].astype(str).unique()
        
        user_idx_map = {user: idx for idx, user in enumerate(users)}
        merchant_idx_map = {merchant: idx + len(users) for idx, merchant in enumerate(merchants)}
        
        graph["user_nodes"] = user_idx_map
        graph["merchant_nodes"] = merchant_idx_map
        
        # Build edges
        for idx, row in df.iterrows():
            user = str(row.get(user_col, "unknown"))
            merchant = str(row.get(merchant_col, "unknown"))
            
            if user not in user_idx_map or merchant not in merchant_idx_map:
                continue
            
            user_idx = user_idx_map[user]
            merchant_idx = merchant_idx_map[merchant]
            
            # Edge features
            amount = float(row.get(amount_col, 0.0) or 0.0)
            distance = float(row.get(distance_col, 0.0) or 0.0)
            
            # Normalize features
            edge_features = [
                np.log1p(amount) / 20.0,  # Normalized log amount
                min(distance / 1000.0, 1.0),  # Normalized distance (max 1000km)
                1.0,  # Edge weight
            ]
            
            graph["edges"].append((user_idx, merchant_idx))
            graph["edge_features"].append(edge_features)
        
        logger.info(f"Built graph with {len(users)} users, {len(merchants)} merchants, {len(graph['edges'])} edges")
        return graph
    
    def compute_node_embeddings(self, graph: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """
        Compute node embeddings using simple aggregation.
        In production, this would use a trained GNN model.
        """
        embeddings = {}
        
        # Aggregate edge features for each node
        node_features = {}
        
        for (src, dst), features in zip(graph["edges"], graph["edge_features"]):
            # Source node (user)
            if src not in node_features:
                node_features[src] = []
            node_features[src].append(features)
            
            # Destination node (merchant)
            if dst not in node_features:
                node_features[dst] = []
            node_features[dst].append(features)
        
        # Compute embeddings as mean of aggregated features
        for node_idx, features_list in node_features.items():
            if features_list:
                aggregated = np.mean(features_list, axis=0)
                # Pad or truncate to embedding_dim
                if len(aggregated) < self.embedding_dim:
                    padded = np.pad(aggregated, (0, self.embedding_dim - len(aggregated)))
                else:
                    padded = aggregated[:self.embedding_dim]
                embeddings[node_idx] = padded
            else:
                embeddings[node_idx] = np.zeros(self.embedding_dim)
        
        return embeddings
    
    def infer_probabilities(self, df: pd.DataFrame) -> np.ndarray:
        """
        Generate fraud probabilities using graph structure.
        
        Returns:
            Array of probabilities [0, 1] for each transaction
        """
        if len(df) == 0:
            return np.zeros((0,), dtype=float)
        
        try:
            # Build graph
            graph = self.build_transaction_graph(df)
            
            # Compute embeddings
            node_embeddings = self.compute_node_embeddings(graph)
            
            # Get node mappings
            user_col = None
            merchant_col = None
            amount_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if "user_id" in col_lower or "sender" in col_lower:
                    user_col = col
                elif "receiver" in col_lower or "merchant" in col_lower:
                    merchant_col = col
                elif "amount" in col_lower and "transaction" in col_lower:
                    amount_col = col
            
            if not user_col:
                user_col = "User_ID"
            if not merchant_col:
                merchant_col = "Receiver_ID"
            if not amount_col:
                amount_col = "Transaction_Amount"
            
            user_idx_map = graph["user_nodes"]
            merchant_idx_map = graph["merchant_nodes"]
            
            # Compute probabilities for each transaction
            probabilities = []
            
            for idx, row in df.iterrows():
                user = str(row.get(user_col, "unknown"))
                merchant = str(row.get(merchant_col, "unknown"))
                amount = float(row.get(amount_col, 0.0) or 0.0)
                
                # Get node indices
                user_idx = user_idx_map.get(user, -1)
                merchant_idx = merchant_idx_map.get(merchant, -1)
                
                # Base probability from amount
                amount_norm = min(amount / 100000.0, 1.0)  # Normalize to 0-1
                
                # Entity risk from embeddings
                user_risk = 0.0
                merchant_risk = 0.0
                
                if user_idx >= 0 and user_idx in node_embeddings:
                    user_embedding = node_embeddings[user_idx]
                    user_risk = float(np.mean(user_embedding)) * 0.5  # Normalize
                
                if merchant_idx >= 0 and merchant_idx in node_embeddings:
                    merchant_embedding = node_embeddings[merchant_idx]
                    merchant_risk = float(np.mean(merchant_embedding)) * 0.5
                
                # Combine risks
                combined_risk = 0.3 * amount_norm + 0.4 * user_risk + 0.3 * merchant_risk
                prob = np.clip(combined_risk, 0.0, 1.0)
                probabilities.append(prob)
            
            return np.array(probabilities)
            
        except Exception as e:
            logger.exception(f"Error computing GNN probabilities: {e}")
            # Fallback to simple heuristic
            return self._fallback_heuristic(df)
    
    def _fallback_heuristic(self, df: pd.DataFrame) -> np.ndarray:
        """Fallback heuristic when graph construction fails."""
        if len(df) == 0:
            return np.zeros((0,), dtype=float)
        
        # Find amount column
        amount_col = None
        for col in df.columns:
            if "amount" in col.lower():
                amount_col = col
                break
        
        if amount_col:
            amounts = pd.to_numeric(df[amount_col], errors='coerce').fillna(0.0)
            # Simple heuristic: higher amount = higher risk
            amounts_norm = (amounts - amounts.min()) / (amounts.max() - amounts.min() + 1e-9)
            return np.clip(0.1 + 0.4 * amounts_norm.values, 0.0, 1.0)
        else:
            return np.zeros((len(df),), dtype=float)
    
    def save_embeddings(self, embeddings: Dict[str, np.ndarray], path: Optional[Path] = None):
        """Save computed embeddings to disk."""
        path = path or self.model_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(embeddings, f)
        logger.info(f"Saved embeddings to {path}")
    
    def load_embeddings(self, path: Optional[Path] = None) -> Optional[Dict[str, np.ndarray]]:
        """Load embeddings from disk."""
        path = path or self.model_path
        if path.exists():
            try:
                with open(path, 'rb') as f:
                    embeddings = pickle.load(f)
                logger.info(f"Loaded embeddings from {path}")
                return embeddings
            except Exception as e:
                logger.warning(f"Failed to load embeddings: {e}")
        return None


# Global instance
gnn_service = GNNService()


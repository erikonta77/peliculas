"""
Cargador del modelo de ML (Autoencoder Keras)
"""

import os
from typing import Optional

import numpy as np
import tensorflow as tf
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger


class ModelLoader:
    """Carga y gestiona el modelo de recomendación."""

    def __init__(self):
        self.model: Optional[tf.keras.Model] = None
        self.encoder: Optional[tf.keras.Model] = None
        self.is_loaded = False

    async def load_model(self, model_path: str = "/app/models/recommender.keras"):
        """Carga el modelo desde disco o crea uno nuevo."""
        try:
            if os.path.exists(model_path):
                logger.info(f"📦 Cargando modelo desde {model_path}")
                self.model = tf.keras.models.load_model(model_path)

                # Extraer encoder (primera mitad del autoencoder)
                # Asumiendo arquitectura: Input -> Dense(64) -> Dense(32) -> Dense(16) -> Dense(32) -> Dense(64) -> Output
                layer_names = [layer.name for layer in self.model.layers]
                logger.info(f"Capas del modelo: {layer_names}")

                # Crear modelo encoder
                if len(self.model.layers) >= 4:
                    # Encoder son las primeras 4 capas (input + 3 densas hasta bottleneck)
                    encoder_output = self.model.layers[3].output
                    self.encoder = tf.keras.Model(
                        inputs=self.model.input,
                        outputs=encoder_output
                    )

                self.is_loaded = True
                logger.info("✅ Modelo cargado exitosamente")
            else:
                logger.warning(f"⚠️ Modelo no encontrado en {model_path}")
                self.is_loaded = False

        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {e}")
            self.is_loaded = False

    async def train_model(self, db: AsyncSession):
        """Entrena el modelo con datos de la base de datos."""
        # TODO: Implementar entrenamiento con datos de PostgreSQL
        logger.info("🏋️ Iniciando entrenamiento del modelo...")
        pass

    def get_embedding(self, features: np.ndarray) -> np.ndarray:
        """Genera embedding a partir de características."""
        if self.encoder is None:
            raise ValueError("Modelo no cargado")

        return self.encoder.predict(features, verbose=0)

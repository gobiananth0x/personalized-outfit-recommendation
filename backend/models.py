from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    google_refresh_token = Column(String(512), nullable=True)
    picture = Column(String(500), nullable=True)
    clothing_items = relationship(
        "ClothingItem", back_populates="owner", cascade="all, delete-orphan"
    )
    outfits = relationship(
        "Outfit", back_populates="user", cascade="all, delete-orphan"
    )


class ClothingItem(Base):
    __tablename__ = "clothing_items"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String(255), nullable=True)
    item_type = Column(String(50), nullable=False, index=True)
    color = Column(String(30), nullable=False, index=True)
    is_available = Column(Boolean, nullable=False, default=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner = relationship("User", back_populates="clothing_items")


class Outfit(Base):
    __tablename__ = "outfits"

    date = Column(Date, primary_key=True, index=True)
    top_id = Column(
        Integer,
        ForeignKey("clothing_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bottom_id = Column(
        Integer,
        ForeignKey("clothing_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    top = relationship("ClothingItem", foreign_keys=[top_id])
    bottom = relationship("ClothingItem", foreign_keys=[bottom_id])
    user = relationship("User", back_populates="outfits")

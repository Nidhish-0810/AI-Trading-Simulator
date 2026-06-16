"""
Leaderboard, achievements, and social trading router.
"""
import uuid
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict

from app.auth.models import User
from app.auth.service import get_all_users_for_leaderboard
from app.core.database import get_db
from app.core.redis_client import get_redis, get_cache, set_cache, CacheKeys
from app.core.security import get_current_active_user
from app.portfolio.models import Holding, Achievement, Follower
from app.trading.models import Trade

logger = logging.getLogger(__name__)
router = APIRouter()

ACHIEVEMENT_DEFS = {
    "first_trade": {"title": "First Blood", "description": "Placed your first trade", "icon": "\u26a1", "xp": 50},
    "ten_trades": {"title": "Active Trader", "description": "Completed 10 trades", "icon": "\U0001f525", "xp": 100},
    "fifty_trades": {"title": "Speed Trader", "description": "Completed 50 trades", "icon": "\U0001f680", "xp": 250},
    "hundred_trades": {"title": "Trade Machine", "description": "Completed 100 trades", "icon": "\U0001f916", "xp": 500},
    "profit_10pct": {"title": "In The Green", "description": "Achieved 10% portfolio return", "icon": "\U0001f4c8", "xp": 200},
    "profit_25pct": {"title": "Strong Performer", "description": "Achieved 25% return", "icon": "\U0001f4b0", "xp": 400},
    "profit_50pct": {"title": "Half-Century", "description": "Achieved 50% return", "icon": "\U0001f3c6", "xp": 750},
    "profit_100pct": {"title": "Doubler", "description": "Doubled your portfolio!", "icon": "\U0001f451", "xp": 1500},
    "diversified_5": {"title": "Diversified", "description": "Hold 5 different stocks", "icon": "\U0001f3af", "xp": 150},
    "diversified_10": {"title": "Well Balanced", "description": "Hold 10 different stocks", "icon": "\U0001f310", "xp": 300},
    "big_win": {"title": "Big Win", "description": "Single trade gain >20%", "icon": "\U0001f3b0", "xp": 300},
    "high_roller": {"title": "High Roller", "description": "Portfolio value exceeded $150,000", "icon": "\U0001f48e", "xp": 600},
    "top_10": {"title": "Elite Trader", "description": "Reached top 10 on leaderboard", "icon": "\U0001f947", "xp": 500},
    "follower_count": {"title": "Influencer", "description": "Gained 5 followers", "icon": "\u2b50", "xp": 200},
}


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    portfolio_value: float
    cash_balance: float
    total_return: float
    total_return_pct: float
    total_trades: int
    is_current_user: bool = False


class FollowResponse(BaseModel):
    following: bool
    message: str


async def _compute_portfolio_value(db: AsyncSession, user: User) -> float:
    result = await db.execute(select(Holding).where(Holding.user_id == user.id))
    holdings = result.scalars().all()
    try:
        import yfinance as yf
        symbols = [h.symbol for h in holdings]
        total_holdings_value = 0.0
        if symbols:
            for h in holdings:
                try:
                    ticker = yf.Ticker(h.symbol)
                    price = float(ticker.fast_info.last_price or h.average_cost)
                    total_holdings_value += float(h.quantity) * price
                except Exception:
                    total_holdings_value += float(h.quantity) * float(h.average_cost)
    except Exception:
        total_holdings_value = sum(float(h.quantity) * float(h.average_cost) for h in holdings)
    return float(user.balance) + total_holdings_value


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    cache_key = CacheKeys.leaderboard("all")
    cached = await get_cache(redis, cache_key)
    if cached:
        for entry in cached:
            entry["is_current_user"] = entry["user_id"] == str(current_user.id)
        return cached
    users = await get_all_users_for_leaderboard(db)
    leaderboard = []
    starting_balance = 100000.0
    for user in users[:50]:
        try:
            portfolio_val = await _compute_portfolio_value(db, user)
            total_return = portfolio_val - starting_balance
            trades_result = await db.execute(select(func.count(Trade.id)).where(Trade.user_id == user.id))
            leaderboard.append({"user_id": str(user.id), "username": user.username, "full_name": user.full_name, "avatar_url": user.avatar_url, "portfolio_value": round(portfolio_val, 2), "cash_balance": float(user.balance), "total_return": round(total_return, 2), "total_return_pct": round(total_return / starting_balance * 100, 2), "total_trades": trades_result.scalar() or 0, "is_current_user": False})
        except Exception as e:
            logger.warning(f"Leaderboard error for {user.username}: {e}")
    leaderboard.sort(key=lambda x: x["total_return_pct"], reverse=True)
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1
    await set_cache(redis, cache_key, leaderboard, ttl=300)
    for entry in leaderboard:
        entry["is_current_user"] = entry["user_id"] == str(current_user.id)
    return leaderboard[:50]


@router.get("/achievements")
async def get_achievements(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Achievement).where(Achievement.user_id == current_user.id))
    earned = result.scalars().all()
    earned_types = {a.achievement_type for a in earned}
    all_achievements = []
    for ach_type, ach_def in ACHIEVEMENT_DEFS.items():
        earned_record = next((a for a in earned if a.achievement_type == ach_type), None)
        all_achievements.append({"achievement_type": ach_type, **ach_def, "earned": ach_type in earned_types, "earned_at": earned_record.created_at.isoformat() if earned_record else None})
    return {"achievements": all_achievements, "earned_count": len(earned_types), "total_count": len(ACHIEVEMENT_DEFS), "total_xp": sum(ACHIEVEMENT_DEFS[t]["xp"] for t in earned_types if t in ACHIEVEMENT_DEFS)}


@router.post("/achievements/check")
async def check_achievements(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Achievement).where(Achievement.user_id == current_user.id))
    already_earned = {a.achievement_type for a in result.scalars().all()}
    newly_earned = []
    trades_result = await db.execute(select(func.count(Trade.id)).where(Trade.user_id == current_user.id))
    trade_count = trades_result.scalar() or 0
    for ach_type, threshold in [("first_trade", 1), ("ten_trades", 10), ("fifty_trades", 50), ("hundred_trades", 100)]:
        if ach_type not in already_earned and trade_count >= threshold:
            db.add(Achievement(user_id=current_user.id, achievement_type=ach_type, title=ACHIEVEMENT_DEFS[ach_type]["title"], description=ACHIEVEMENT_DEFS[ach_type]["description"]))
            newly_earned.append(ach_type)
    portfolio_val = await _compute_portfolio_value(db, current_user)
    roi = (portfolio_val - 100000.0) / 100000.0 * 100
    for ach_type, threshold in [("profit_10pct", 10), ("profit_25pct", 25), ("profit_50pct", 50), ("profit_100pct", 100)]:
        if ach_type not in already_earned and roi >= threshold:
            db.add(Achievement(user_id=current_user.id, achievement_type=ach_type, title=ACHIEVEMENT_DEFS[ach_type]["title"], description=ACHIEVEMENT_DEFS[ach_type]["description"]))
            newly_earned.append(ach_type)
    if "high_roller" not in already_earned and portfolio_val >= 150000:
        db.add(Achievement(user_id=current_user.id, achievement_type="high_roller", title=ACHIEVEMENT_DEFS["high_roller"]["title"], description=ACHIEVEMENT_DEFS["high_roller"]["description"]))
        newly_earned.append("high_roller")
    holdings_result = await db.execute(select(func.count(Holding.id)).where(Holding.user_id == current_user.id))
    hc = holdings_result.scalar() or 0
    for ach_type, threshold in [("diversified_5", 5), ("diversified_10", 10)]:
        if ach_type not in already_earned and hc >= threshold:
            db.add(Achievement(user_id=current_user.id, achievement_type=ach_type, title=ACHIEVEMENT_DEFS[ach_type]["title"], description=ACHIEVEMENT_DEFS[ach_type]["description"]))
            newly_earned.append(ach_type)
    await db.flush()
    return {"newly_earned": [{"type": t, **ACHIEVEMENT_DEFS.get(t, {})} for t in newly_earned], "count": len(newly_earned)}


@router.post("/social/follow/{user_id}", response_model=FollowResponse)
async def follow_user(user_id: uuid.UUID, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    existing = await db.execute(select(Follower).where(and_(Follower.follower_id == current_user.id, Follower.following_id == user_id)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already following this user")
    db.add(Follower(follower_id=current_user.id, following_id=user_id))
    await db.flush()
    return FollowResponse(following=True, message="Successfully followed user")


@router.delete("/social/follow/{user_id}", response_model=FollowResponse)
async def unfollow_user(user_id: uuid.UUID, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Follower).where(and_(Follower.follower_id == current_user.id, Follower.following_id == user_id)))
    follow = result.scalar_one_or_none()
    if not follow:
        raise HTTPException(status_code=404, detail="Not following this user")
    await db.delete(follow)
    return FollowResponse(following=False, message="Unfollowed successfully")


@router.get("/social/followers")
async def get_followers(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Follower, User).join(User, User.id == Follower.follower_id).where(Follower.following_id == current_user.id))
    rows = result.all()
    return {"followers": [{"user_id": str(u.id), "username": u.username, "avatar_url": u.avatar_url} for _, u in rows], "count": len(rows)}


@router.get("/social/following")
async def get_following(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Follower, User).join(User, User.id == Follower.following_id).where(Follower.follower_id == current_user.id))
    rows = result.all()
    return {"following": [{"user_id": str(u.id), "username": u.username, "avatar_url": u.avatar_url} for _, u in rows], "count": len(rows)}

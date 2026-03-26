"""
Profile repository for database operations
"""
from datetime import datetime
from typing import Optional
import json

from db.database import get_db, execute_and_commit, fetch_one, fetch_all
from db.models import Profile, ProfileCreate, ProfileUpdate, ProfileWithActions


class ProfileRepository:
    """Repository for profile database operations"""

    async def get_all(self) -> list[Profile]:
        """Get all profiles"""
        query = '''
            SELECT user_id, serial_number, name, domain_name, group_id, group_name,
                   created_time, last_open_time, ip, ip_country,
                   followers_count, following_count, bio, location, last_updated
            FROM profiles
            ORDER BY serial_number
        '''
        rows = await fetch_all(query)
        return [Profile(**dict(row)) for row in rows]

    async def get_by_id(self, user_id: str) -> Optional[Profile]:
        """Get profile by user_id"""
        query = '''
            SELECT user_id, serial_number, name, domain_name, group_id, group_name,
                   created_time, last_open_time, ip, ip_country,
                   followers_count, following_count, bio, location, last_updated
            FROM profiles
            WHERE user_id = ?
        '''
        row = await fetch_one(query, (user_id,))
        if row:
            return Profile(**dict(row))
        return None

    async def get_by_serial(self, serial_number: str) -> Optional[Profile]:
        """Get profile by serial number"""
        query = '''
            SELECT user_id, serial_number, name, domain_name, group_id, group_name,
                   created_time, last_open_time, ip, ip_country,
                   followers_count, following_count, bio, location, last_updated
            FROM profiles
            WHERE serial_number = ?
        '''
        row = await fetch_one(query, (serial_number,))
        if row:
            return Profile(**dict(row))
        return None

    async def create(self, profile: ProfileCreate) -> Profile:
        """Create a new profile"""
        query = '''
            INSERT INTO profiles (user_id, serial_number, name, domain_name,
                                  group_id, group_name, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        await execute_and_commit(query, (
            profile.user_id,
            profile.serial_number,
            profile.name,
            profile.domain_name,
            profile.group_id,
            profile.group_name,
            datetime.now()
        ))
        return await self.get_by_id(profile.user_id)

    async def update(self, user_id: str, profile: ProfileUpdate) -> Optional[Profile]:
        """Update a profile"""
        updates = []
        params = []

        if profile.name is not None:
            updates.append("name = ?")
            params.append(profile.name)
        if profile.followers_count is not None:
            updates.append("followers_count = ?")
            params.append(profile.followers_count)
        if profile.following_count is not None:
            updates.append("following_count = ?")
            params.append(profile.following_count)
        if profile.ip is not None:
            updates.append("ip = ?")
            params.append(profile.ip)
        if profile.ip_country is not None:
            updates.append("ip_country = ?")
            params.append(profile.ip_country)

        if not updates:
            return await self.get_by_id(user_id)

        updates.append("last_updated = ?")
        params.append(datetime.now())
        params.append(user_id)

        query = f"UPDATE profiles SET {', '.join(updates)} WHERE user_id = ?"
        await execute_and_commit(query, tuple(params))
        return await self.get_by_id(user_id)

    async def upsert_from_adspower(self, profile_data: dict) -> Profile:
        """Insert or update profile from AdsPower data"""
        user_id = profile_data.get('user_id', '')
        existing = await self.get_by_id(user_id)

        if existing:
            # Update but preserve followers/following counts and last_updated (Twitter stats time)
            query = '''
                UPDATE profiles
                SET serial_number = ?, name = ?, domain_name = ?, group_id = ?,
                    group_name = ?, created_time = ?, last_open_time = ?,
                    ip = ?, ip_country = ?
                WHERE user_id = ?
            '''
            await execute_and_commit(query, (
                profile_data.get('serial_number', ''),
                profile_data.get('name', ''),
                profile_data.get('domain_name', ''),
                profile_data.get('group_id', ''),
                profile_data.get('group_name', ''),
                profile_data.get('created_time', ''),
                profile_data.get('last_open_time', ''),
                profile_data.get('ip', ''),
                profile_data.get('ip_country', ''),
                user_id
            ))
        else:
            # Insert new profile with NULL last_updated (not yet fetched from Twitter)
            query = '''
                INSERT INTO profiles
                (user_id, serial_number, name, domain_name, group_id, group_name,
                 created_time, last_open_time, ip, ip_country,
                 followers_count, following_count, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, NULL)
            '''
            await execute_and_commit(query, (
                user_id,
                profile_data.get('serial_number', ''),
                profile_data.get('name', ''),
                profile_data.get('domain_name', ''),
                profile_data.get('group_id', ''),
                profile_data.get('group_name', ''),
                profile_data.get('created_time', ''),
                profile_data.get('last_open_time', ''),
                profile_data.get('ip', ''),
                profile_data.get('ip_country', '')
            ))

        return await self.get_by_id(user_id)

    async def get_with_actions(self, user_id: str) -> Optional[ProfileWithActions]:
        """Get profile with action summary"""
        profile = await self.get_by_id(user_id)
        if not profile:
            return None

        # Get action summary
        query = '''
            SELECT action_type, action_name,
                   SUM(assigned_count) as total_assigned,
                   SUM(completed_count) as total_completed,
                   SUM(failed_count) as total_failed
            FROM actions
            WHERE profile_id = ?
            GROUP BY action_type, action_name
        '''
        rows = await fetch_all(query, (user_id,))

        actions = {}
        total_assigned = 0
        total_completed = 0
        total_failed = 0

        for row in rows:
            key = f"{row['action_type']}_{row['action_name']}"
            actions[key] = {
                'assigned': row['total_assigned'],
                'completed': row['total_completed'],
                'failed': row['total_failed']
            }
            total_assigned += row['total_assigned'] or 0
            total_completed += row['total_completed'] or 0
            total_failed += row['total_failed'] or 0

        success_rate = (total_completed / total_assigned * 100) if total_assigned > 0 else 0.0

        return ProfileWithActions(
            **profile.model_dump(),
            actions=actions,
            total_assigned=total_assigned,
            total_completed=total_completed,
            total_failed=total_failed,
            success_rate=success_rate
        )

    async def update_followers_following(
        self,
        user_id: str,
        followers_count: int,
        following_count: int,
        bio: str = None,
        location: str = None
    ) -> Optional[Profile]:
        """Update followers, following counts, bio, and location"""
        query = '''
            UPDATE profiles
            SET followers_count = ?, following_count = ?, bio = ?, location = ?, last_updated = ?
            WHERE user_id = ?
        '''
        await execute_and_commit(query, (
            followers_count, following_count, bio or '', location or '', datetime.now(), user_id
        ))
        return await self.get_by_id(user_id)

    async def delete(self, user_id: str) -> bool:
        """Delete a profile"""
        query = "DELETE FROM profiles WHERE user_id = ?"
        await execute_and_commit(query, (user_id,))
        return True

    async def get_count(self) -> int:
        """Get total profile count"""
        query = "SELECT COUNT(*) as count FROM profiles"
        row = await fetch_one(query)
        return row['count'] if row else 0

import logging
from typing import Optional, Dict, Any
from util.database_util import DatabaseUtil

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SiteMasterRepository:
    def get_site_master_by_id(self, site_master_id: str) -> Optional[Dict[str, Any]]:
        """
        Get site master details by site_master_id.
        
        Args:
            site_master_id (str): The ID of the site master to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Site master details if found, None otherwise
        """
        try:
            with DatabaseUtil.connection() as connection:
                with connection.cursor() as cursor:
                    query = """
                        SELECT *
                        FROM SITE_MASTER 
                        WHERE SITE_MASTER_ID = %s;
                    """
                    
                    DatabaseUtil.execute(cursor, query, (site_master_id,))
                    result = cursor.fetchone()
                    
                    if result:
                        logger.info(f"Found site master with ID: {site_master_id}")
                        return result
                    else:
                        logger.info(f"No site master found with ID: {site_master_id}")
                        return None
                    
        except Exception as e:
            logger.error(f"Error fetching site master: {e}")
            raise

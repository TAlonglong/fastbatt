# SPDX-License-Identifier: BSD-3-Clause

# flake8: noqa F401
from collections.abc import Callable

import numpy as np

from vendeeglobe import (
    Checkpoint,
    Heading,
    Instructions,
    Location,
    Vector,
    config,
)
from vendeeglobe.utils import distance_on_surface


class Bot:
    """
    This is the ship-controlling bot that will be instantiated for the competition.
    """

    def __init__(self):
        self.team = "Fast Bått"  # This is your team name
        # This is the course that the ship has to follow
        self.course = [
            Checkpoint(latitude=17.38, longitude=-68.9  , radius=10),
            Checkpoint(latitude=9.35529, longitude=-80.593349, radius=50),
            Checkpoint(latitude=8.82625, longitude=-79.64060, radius=5),
            Checkpoint(latitude=8.83, longitude=-79.48, radius=20),
            Checkpoint(latitude=4.50, longitude=-79.25, radius=50),
            # Checkpoint(latitude=43.797109, longitude=-11.264905, radius=50),
            # Checkpoint(longitude=-29.908577, latitude=17.999811, radius=50),
            # Checkpoint(latitude=-11.441808, longitude=-29.660252, radius=50),
            # Checkpoint(longitude=-63.240264, latitude=-61.025125, radius=50),
            Checkpoint(latitude=2.806318, longitude=-168.943864, radius=1990.0),
            Checkpoint(latitude=-62.052286, longitude=169.214572, radius=50.0),
            Checkpoint(latitude=-15.668984, longitude=77.674694, radius=1190.0),
            Checkpoint(latitude=-39.438937, longitude=19.836265, radius=50.0),
            Checkpoint(latitude=14.881699, longitude=-21.024326, radius=50.0),
            Checkpoint(latitude=44.076538, longitude=-18.292936, radius=50.0),
            Checkpoint(
                latitude=config.start.latitude,
                longitude=config.start.longitude,
                radius=5,
            ),
            
        ]

    def run(
        self,
        t: float,
        dt: float,
        longitude: float,
        latitude: float,
        heading: float,
        speed: float,
        vector: np.ndarray,
        forecast: Callable,
        world_map: Callable,
    ) -> Instructions:
        """
        This is the method that will be called at every time step to get the
        instructions for the ship.

        Parameters
        ----------
        t:
            The current time in hours.
        dt:
            The time step in hours.
        longitude:
            The current longitude of the ship.
        latitude:
            The current latitude of the ship.
        heading:
            The current heading of the ship.
        speed:
            The current speed of the ship.
        vector:
            The current heading of the ship, expressed as a vector.
        forecast:
            Method to query the weather forecast for the next 5 days.
            Example:
            current_position_forecast = forecast(
                latitudes=latitude, longitudes=longitude, times=0
            )
        world_map:
            Method to query map of the world: 1 for sea, 0 for land.
            Example:
            current_position_terrain = world_map(
                latitudes=latitude, longitudes=longitude
            )

        Returns
        -------
        instructions:
            A set of instructions for the ship. This can be:
            - a Location to go to
            - a Heading to point to
            - a Vector to follow
            - a number of degrees to turn Left
            - a number of degrees to turn Right

            Optionally, a sail value between 0 and 1 can be set.
        """
        # Initialize the instructions
        instructions = Instructions()

        # TODO: Remove this, it's only for testing =================
        current_position_forecast = forecast(
            latitudes=latitude, longitudes=longitude, times=0
        )
        current_position_terrain = world_map(latitudes=latitude, longitudes=longitude)
        # ===========================================================

        # changed_diretion = False
        # # Check for nearby land using the world_map function
        # if world_map(latitudes=latitude, longitudes=longitude) == 0:  # Land detected
        #     instructions.heading = (heading + 90) % 360  # Adjust to avoid land
        #     changed_diretion= True
        # if changed_diretion and world_map(latitudes=latitude, longitudes=longitude) == 1:
        #     instructions.heading = (heading - 90) % 360  # Adjust to avoid land
        #     changed_diretion= False
        
        # Check the current position for land
        terrain = world_map(latitudes=latitude, longitudes=longitude)

        if terrain == 0:  # If land detected
            # Check alternative headings in increments (e.g., every 45 degrees)
            for angle_offset in range(0, 360, 45):
                new_heading = (heading + angle_offset) % 360
                # Calculate a point a short distance along this heading
                test_longitude = longitude + 0.01 * np.cos(np.radians(new_heading))
                test_latitude = latitude + 0.01 * np.sin(np.radians(new_heading))
                # Check if this new point is over water
                if world_map(latitudes=test_latitude, longitudes=test_longitude) == 1:
                    instructions.heading = new_heading  # Update heading to avoid land
                    break

        # Go through all checkpoints and find the next one to reach
        for ch in self.course:
            # Compute the distance to the checkpoint
            dist = distance_on_surface(
                longitude1=longitude,
                latitude1=latitude,
                longitude2=ch.longitude,
                latitude2=ch.latitude,
            )
            # Consider slowing down if the checkpoint is close
            jump = dt * np.linalg.norm(speed)
            if dist < 2.0 * ch.radius + jump:
                instructions.sail = min(ch.radius / jump, 1)
            else:
                instructions.sail = 1.0
            # Check if the checkpoint has been reached
            if dist < ch.radius:
                ch.reached = True
            if not ch.reached:
                instructions.location = Location(
                    longitude=ch.longitude, latitude=ch.latitude
                )
                break

        return instructions

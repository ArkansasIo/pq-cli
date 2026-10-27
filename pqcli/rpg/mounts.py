from dataclasses import dataclass, field


@dataclass(frozen=True)
class Mount:
    id: str
    name: str
    speed_multiplier: float = 1.25
    flying: bool = False


@dataclass
class MountCollection:
    mounts: dict[str, Mount] = field(default_factory=dict)
    active_mount: str | None = None

    def add(self, mount: Mount) -> None:
        self.mounts[mount.id] = mount

    def summon(self, mount_id: str) -> bool:
        if mount_id not in self.mounts:
            return False
        self.active_mount = mount_id
        return True

    def dismiss(self) -> None:
        self.active_mount = None
